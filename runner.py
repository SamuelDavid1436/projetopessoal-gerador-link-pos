# -*- coding: utf-8 -*-
"""
runner.py
Distribui os itens (CPFs) entre os perfis selecionados, rodando em
paralelo (threads). Cuida de:
  - reinício automático do navegador se a sessão morrer;
  - retry automático em timeout de item específico;
  - botão "Parar" que nunca corta um item no meio;
  - callbacks de início/resultado por item pra alimentar o dashboard.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from selenium.common.exceptions import TimeoutException, WebDriverException

import config
import crm_client
import browser_manager
import perfis as perfis_mod
import recuperacao as recuperacao_mod

logger = logging.getLogger("runner")


@dataclass
class ResultadoItem:
    cpf: str
    linhas: List[Dict] = field(default_factory=list)
    sucesso: bool = False
    erro: str = ""


class Runner:
    def __init__(
        self,
        perfis_selecionados: List[perfis_mod.Perfil],
        itens: List[str],
        gerenciador_perfis: perfis_mod.GerenciadorPerfis,
        pasta_saida: str,
        exec_id: str,
        callback_inicio_item: Optional[Callable[[str, str], None]] = None,
        callback_resultado_item: Optional[Callable[[ResultadoItem, str], None]] = None,
        telefones: Optional[Dict[str, str]] = None,
    ):
        self.perfis_selecionados = perfis_selecionados
        self.fila = queue.Queue()
        for item in itens:
            self.fila.put(item)
        self.total_itens = len(itens)
        self.gerenciador_perfis = gerenciador_perfis
        self.pasta_saida = pasta_saida
        self.exec_id = exec_id
        self.callback_inicio_item = callback_inicio_item
        self.callback_resultado_item = callback_resultado_item
        # CPF -> telefone informado na base de entrada (tem prioridade sobre
        # o telefone lido na plataforma)
        self.telefones = telefones or {}

        self.log_recuperacao = recuperacao_mod.LogRecuperacao()
        self.log_recuperacao.iniciar(exec_id, pasta_saida, self.total_itens)

        self._parar_evento = threading.Event()
        self._lock_contadores = threading.Lock()
        self.processados = 0
        self.sucessos = 0
        self.erros = 0
        self.resultados: List[Dict] = []

    # ------------------------------------------------------------------
    def parar(self):
        """Sinaliza para os workers pararem. Nunca interrompe um item em
        andamento — cada worker termina o item atual antes de checar isto."""
        self._parar_evento.set()

    @property
    def foi_interrompido(self) -> bool:
        return self._parar_evento.is_set()

    # ------------------------------------------------------------------
    def _worker(self, perfil: perfis_mod.Perfil):
        try:
            self._worker_interno(perfil)
        except Exception:  # noqa: BLE001 - erro inesperado não pode sumir em silêncio
            logger.exception("Perfil %s: erro inesperado no processamento.", perfil.apelido)

    def _worker_interno(self, perfil: perfis_mod.Perfil):
        if browser_manager.perfil_tem_navegador_aberto(perfil.id):
            logger.error(
                "Perfil %s tem uma janela de login manual aberta — pulando pra evitar "
                "dois navegadores disputando a mesma pasta de perfil. Feche a janela de "
                "login e tente novamente.", perfil.apelido,
            )
            return

        logger.info("Perfil %s: abrindo o Chrome...", perfil.apelido)
        nav = browser_manager.NavegadorPerfil(perfil)
        try:
            driver = nav.abrir()
        except Exception as e:  # noqa: BLE001 - qualquer falha ao abrir vai pro log
            logger.error(
                "Falha ao abrir o Chrome do perfil %s: %s. Feche todas as janelas do Chrome "
                "abertas pelo programa e tente de novo; confira se o Chrome está atualizado.",
                perfil.apelido, e,
            )
            return
        logger.info("Perfil %s: Chrome aberto, verificando login...", perfil.apelido)

        # Nunca tenta buscar CPF sem login confirmado antes — evita uma
        # cascata de erros logo no primeiro item se a sessão tiver caído.
        try:
            login_ok = browser_manager.garantir_login_para_execucao(driver, perfil)
        except WebDriverException as e:
            logger.error("Perfil %s: falha ao verificar/realizar login (%s).", perfil.apelido, e)
            nav.fechar()
            return

        if not login_ok:
            logger.error(
                "Perfil %s: login não confirmado — nenhum CPF será processado com esse "
                "perfil nesta execução. Faça 'Login manual' na tela Perfis primeiro.",
                perfil.apelido,
            )
            nav.fechar()
            return

        tentativas_sessao = 0

        while not self._parar_evento.is_set():
            try:
                cpf = self.fila.get_nowait()
            except queue.Empty:
                break

            if self.callback_inicio_item:
                self.callback_inicio_item(cpf, perfil.apelido)

            resultado = self._processar_item_com_retry(driver, cpf, perfil)

            # se a sessão morreu de vez, tenta reiniciar o navegador (até N vezes)
            if resultado is None:
                tentativas_sessao += 1
                if tentativas_sessao > config.MAX_TENTATIVAS_SESSAO:
                    logger.error("Perfil %s: excedeu tentativas de reinício de sessão.", perfil.apelido)
                    self.fila.put(cpf)  # devolve o item pra outro perfil pegar
                    break
                try:
                    driver = nav.reiniciar()
                    continue
                except WebDriverException:
                    self.fila.put(cpf)
                    break

            self._registrar_resultado(resultado)

            if self.callback_resultado_item:
                self.callback_resultado_item(resultado, perfil.apelido)

            self.fila.task_done()

        # nunca fecha o navegador no meio de um item — só ao sair do loop
        nav.fechar()

    # ------------------------------------------------------------------
    def _processar_item_com_retry(self, driver, cpf: str, perfil: perfis_mod.Perfil) -> Optional[ResultadoItem]:
        """Tenta processar o item até MAX_TENTATIVAS_ITEM vezes em caso de
        timeout (atualiza a página e tenta de novo). Não repete em outros
        tipos de erro. Retorna None se a sessão do navegador morreu."""
        for tentativa in range(1, config.MAX_TENTATIVAS_ITEM + 1):
            try:
                linhas = crm_client.processar_cpf(driver, cpf)
                return ResultadoItem(cpf=cpf, linhas=linhas, sucesso=True)

            except crm_client.ItemNaoEncontradoError as e:
                caminho_print = crm_client._salvar_screenshot_erro(driver, cpf, "nao_encontrado")
                linha_erro = self._linha_erro(cpf, str(e))
                return ResultadoItem(cpf=cpf, linhas=[linha_erro], sucesso=False, erro=str(e))

            except TimeoutException as e:
                logger.warning("Timeout no item %s (tentativa %s/%s)", cpf, tentativa, config.MAX_TENTATIVAS_ITEM)
                if tentativa < config.MAX_TENTATIVAS_ITEM:
                    try:
                        driver.refresh()
                        time.sleep(1.5)
                    except WebDriverException:
                        pass
                    continue
                caminho_print = crm_client._salvar_screenshot_erro(driver, cpf, "timeout")
                linha_erro = self._linha_erro(cpf, f"Timeout após {config.MAX_TENTATIVAS_ITEM} tentativas")
                return ResultadoItem(cpf=cpf, linhas=[linha_erro], sucesso=False, erro="timeout")

            except WebDriverException as e:
                if browser_manager.sessao_esta_morta(e):
                    logger.error("Sessão morta no perfil %s durante item %s.", perfil.apelido, cpf)
                    return None  # sinaliza pro worker reiniciar o navegador
                caminho_print = crm_client._salvar_screenshot_erro(driver, cpf, "erro_navegador")
                linha_erro = self._linha_erro(cpf, str(e))
                return ResultadoItem(cpf=cpf, linhas=[linha_erro], sucesso=False, erro=str(e))

            except Exception as e:  # noqa: BLE001 - erro inesperado, registra e segue
                logger.exception("Erro inesperado processando %s", cpf)
                caminho_print = crm_client._salvar_screenshot_erro(driver, cpf, "erro_inesperado")
                linha_erro = self._linha_erro(cpf, str(e))
                return ResultadoItem(cpf=cpf, linhas=[linha_erro], sucesso=False, erro=str(e))

        return None

    @staticmethod
    def _linha_erro(cpf: str, observacao: str) -> Dict:
        return {
            "CPF": cpf,
            "Nome": "",
            "Situacao_Matricula": "",
            "Curso": "",
            "Plano": "",
            "Email": "",
            "Telefone": "",
            "Mes_Ano": "",
            "Valor_Pago": "",
            "Vencimento": "",
            "Situacao_Parcela": "",
            "Link_Pagamento": "",
            "Status_Processamento": "Erro",
            "Observacao": observacao,
        }

    # ------------------------------------------------------------------
    def _registrar_resultado(self, resultado: ResultadoItem):
        telefone_base = (self.telefones.get(resultado.cpf) or "").strip()
        if telefone_base:
            for linha in resultado.linhas:
                linha["Telefone"] = telefone_base
        with self._lock_contadores:
            self.processados += 1
            if resultado.sucesso:
                self.sucessos += 1
            else:
                self.erros += 1
            self.resultados.extend(resultado.linhas)
        self.log_recuperacao.registrar_resultado({
            "cpf": resultado.cpf,
            "sucesso": resultado.sucesso,
            "linhas": resultado.linhas,
        })

    # ------------------------------------------------------------------
    def executar(self):
        """Roda os workers em paralelo (uma thread por perfil selecionado)
        e bloqueia até todos terminarem."""
        threads = []
        for perfil in self.perfis_selecionados:
            t = threading.Thread(target=self._worker, args=(perfil,), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.log_recuperacao.limpar()
        return self.resultados
