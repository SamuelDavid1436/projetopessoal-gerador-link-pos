# -*- coding: utf-8 -*-
"""
limpeza.py
"Zerar painel": deixa o programa como novo antes de começar outro polo.
Apaga estatísticas, histórico de execuções, recuperação pendente, todas as
pastas de saída e as imagens de erro. NÃO mexe em perfis, logins salvos
nem nas sessões do Chrome.
"""

import logging
import os
import shutil
from typing import Dict

import config

logger = logging.getLogger("limpeza")


def _apagar_conteudo(pasta: str) -> Dict[str, int]:
    """Apaga tudo dentro de `pasta` (mantém a pasta). Conta o que não deu
    pra apagar — normalmente arquivo aberto no Excel."""
    apagados, falhas = 0, 0
    if not os.path.isdir(pasta):
        return {"apagados": 0, "falhas": 0}
    for nome in os.listdir(pasta):
        caminho = os.path.join(pasta, nome)
        try:
            if os.path.isdir(caminho) and not os.path.islink(caminho):
                shutil.rmtree(caminho)
            else:
                os.remove(caminho)
            apagados += 1
        except OSError as e:
            falhas += 1
            logger.warning("Não foi possível apagar %s: %s", caminho, e)
    return {"apagados": apagados, "falhas": falhas}


def zerar_tudo(app) -> Dict[str, int]:
    """Zera números do painel, histórico, recuperação, pastas de saída e
    screenshots. Retorna quantas pastas de saída foram apagadas e quantos
    itens falharam."""
    app.estatisticas.zerar()
    app.historico.registros = []
    app.historico.salvar()
    app.log_recuperacao.limpar()

    saida = _apagar_conteudo(config.DIR_SAIDA)
    prints = _apagar_conteudo(config.DIR_SCREENSHOTS)

    logger.info(
        "Painel zerado: %s pasta(s) de saída apagada(s), %s imagem(ns) de erro apagada(s), %s falha(s).",
        saida["apagados"], prints["apagados"], saida["falhas"] + prints["falhas"],
    )
    return {"pastas_saida": saida["apagados"], "falhas": saida["falhas"] + prints["falhas"]}


def zerar_painel_com_confirmacao(app):
    """Fluxo completo do botão 'Zerar painel': confirma, limpa e atualiza
    as telas. Usado na tela Início e na seção Zerar painel de Configurações."""
    import tkinter.messagebox as messagebox

    if app.runner_ativo is not None:
        messagebox.showwarning("Execução em andamento", "Pare ou aguarde a execução terminar antes de zerar o painel.")
        return
    confirmar = messagebox.askyesno(
        "Zerar painel",
        "Isso vai apagar:\n\n"
        "• os números do painel e o histórico de execuções;\n"
        "• TODAS as pastas de saída (resultado, base_disparo etc.);\n"
        "• as imagens de erro.\n\n"
        "Perfis e logins salvos NÃO são apagados.\n\n"
        "Se precisar dos arquivos gerados, copie-os antes.\n\n"
        "Deseja continuar?",
        icon="warning",
    )
    if not confirmar:
        return

    resultado = zerar_tudo(app)

    pagina_execucoes = app.paginas.get("Execuções")
    if pagina_execucoes:
        pagina_execucoes.caminho_base_selecionada = None
        pagina_execucoes.rotulo_arquivo.configure(text="  nenhum arquivo selecionado")
        pagina_execucoes._atualizar_historico()
    pagina_inicio = app.paginas.get("Início")
    if pagina_inicio:
        pagina_inicio.resetar_execucao_ui()
        pagina_inicio.ao_exibir()

    if resultado["falhas"]:
        messagebox.showwarning(
            "Painel zerado com pendências",
            f"Alguns arquivos não puderam ser apagados ({resultado['falhas']}). "
            "Feche o Excel ou outros programas usando esses arquivos e clique em Zerar painel de novo.",
        )
    else:
        messagebox.showinfo("Painel zerado", "Tudo limpo. Pode começar a próxima execução.")
