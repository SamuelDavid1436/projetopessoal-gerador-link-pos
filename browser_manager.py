# -*- coding: utf-8 -*-
"""
browser_manager.py
Gestão de perfis do Chrome: cada perfil abre com seu próprio
--user-data-dir independente, permitindo até 3 logins simultâneos.
Também cuida da detecção automática de e-mail no campo de login da
Microsoft, usada para preencher o apelido do perfil.

IMPORTANTE — trava de perfil: o Chrome não permite que dois processos
usem a mesma pasta de --user-data-dir ao mesmo tempo. Se isso acontecer
(ex.: clicar em "Login manual" duas vezes, ou abrir "Verificar login"
enquanto uma janela de login manual do mesmo perfil ainda está aberta), o
Chrome pode abrir uma sessão temporária que NÃO persiste nada em disco —
o usuário loga normalmente, mas nada é salvo de verdade. Por isso este
módulo mantém um registro de qual perfil já tem um navegador aberto, e
recusa abrir um segundo antes do primeiro ser fechado.
"""

import logging
import threading
import time
from typing import Optional, Dict

# Import direto da classe do Chrome: o `selenium.webdriver` das versões
# novas carrega os navegadores de forma "preguiçosa", e o PyInstaller não
# enxerga esse import — o .exe quebrava com "No module named
# 'selenium.webdriver.chrome.webdriver'".
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

import config
import perfis as perfis_mod
import credenciais as credenciais_mod

logger = logging.getLogger("browser_manager")

ERROS_SESSAO_MORTA = (
    "invalid session id",
    "chrome not reachable",
    "session deleted",
    "disconnected",
    "target window already closed",
)

# Registro de navegadores atualmente abertos, por ID de perfil — garante
# que nunca haja dois processos do Chrome disputando a mesma pasta.
_navegadores_ativos: Dict[int, "NavegadorPerfil"] = {}
_lock_registro = threading.Lock()


def perfil_tem_navegador_aberto(perfil_id: int) -> bool:
    with _lock_registro:
        nav = _navegadores_ativos.get(perfil_id)
        return nav is not None and nav.driver is not None


def sessao_esta_morta(excecao: Exception) -> bool:
    texto = str(excecao).lower()
    return any(marca in texto for marca in ERROS_SESSAO_MORTA)


class NavegadorPerfil:
    """Encapsula um driver do Chrome atrelado a um perfil específico."""

    def __init__(self, perfil: perfis_mod.Perfil):
        self.perfil = perfil
        self.driver: Optional[ChromeDriver] = None

    def abrir(self, headless: bool = False):
        opcoes = Options()
        opcoes.add_argument(f"--user-data-dir={self.perfil.pasta_dados}")
        opcoes.add_argument("--profile-directory=Default")
        opcoes.add_argument("--no-first-run")
        opcoes.add_argument("--no-default-browser-check")
        opcoes.add_argument("--disable-notifications")
        opcoes.add_argument("--start-maximized")
        opcoes.add_experimental_option("excludeSwitches", ["enable-logging"])
        if headless:
            opcoes.add_argument("--headless=new")

        self.driver = ChromeDriver(options=opcoes)
        self.driver.set_page_load_timeout(config.TIMEOUT_LONGO)
        with _lock_registro:
            _navegadores_ativos[self.perfil.id] = self
        return self.driver

    def fechar(self):
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
            finally:
                self.driver = None
        with _lock_registro:
            if _navegadores_ativos.get(self.perfil.id) is self:
                del _navegadores_ativos[self.perfil.id]

    def reiniciar(self, headless: bool = False):
        self.fechar()
        time.sleep(1)
        return self.abrir(headless=headless)


class PerfilEmUsoError(Exception):
    """Levantada ao tentar abrir um segundo navegador pro mesmo perfil
    enquanto o primeiro ainda está aberto (evitaria a trava de perfil do
    Chrome e a perda silenciosa de login)."""


class LoginNecessarioError(Exception):
    """Levantada quando uma execução precisa de login e não há sessão
    válida nem credenciais salvas pra logar automaticamente."""


def _preencher_e_submeter_login(driver, usuario: str, senha: str) -> bool:
    """Preenche o formulário nativo de login da Plataforma Kroton
    (usuário/senha) e envia. Retorna True se o envio foi feito (não
    garante sucesso — quem chama deve aguardar/confirmar o redirecionamento)."""
    try:
        campo_usuario = WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config.SEL_CAMPO_USUARIO))
        )
        campo_senha = driver.find_element(By.CSS_SELECTOR, config.SEL_CAMPO_SENHA)
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)
        campo_senha.clear()
        campo_senha.send_keys(senha)
        botao_entrar = driver.find_element(By.CSS_SELECTOR, config.SEL_BOTAO_ENTRAR)
        botao_entrar.click()
        return True
    except (TimeoutException, NoSuchElementException, WebDriverException):
        logger.exception("Falha ao preencher/submeter o formulário de login.")
        return False


def _aguardar_redirecionamento_pos_login(driver, timeout: int = config.TIMEOUT_PADRAO) -> bool:
    """Aguarda a URL sair da tela de login, confirmando que o login deu
    certo. Ignora exceções transitórias que podem ocorrer durante o
    recarregamento completo da página (formulário tradicional, não SPA)
    — só timeout genuíno conta como falha."""
    try:
        WebDriverWait(driver, timeout, ignored_exceptions=(WebDriverException,)).until(
            lambda d: "login" not in d.current_url
        )
        return True
    except TimeoutException:
        return False


def login_manual(perfil: perfis_mod.Perfil, gerenciador: perfis_mod.GerenciadorPerfis) -> "NavegadorPerfil":
    """Abre o navegador do perfil na tela de login. Se já houver
    usuário/senha salvos pra esse perfil (cofre do sistema operacional),
    preenche e envia o formulário automaticamente — sem precisar de
    digitação manual. Se for a primeira vez, aguarda o usuário digitar
    manualmente, monitora os campos de usuário/senha em tempo real, e
    salva as credenciais assim que o login é confirmado (redirecionamento
    pra fora da tela de login). O apelido do perfil também é atualizado
    pro usuário digitado. Fecha sozinho pouco depois de confirmar o
    login, pra garantir que a sessão seja gravada em disco e a pasta do
    perfil seja liberada pra próximas verificações/execuções.

    Levanta PerfilEmUsoError se já existir um navegador aberto pra esse
    mesmo perfil — nunca abre um segundo (isso é o que causava login
    "não salvando": dois processos do Chrome brigando pela mesma pasta)."""
    if perfil_tem_navegador_aberto(perfil.id):
        raise PerfilEmUsoError(
            f"Já existe uma janela de login aberta para o perfil '{perfil.apelido}'. "
            "Feche ou finalize o login nela antes de abrir outra."
        )

    nav = NavegadorPerfil(perfil)
    driver = nav.abrir()
    driver.get(config.URL_LOGIN)

    gerenciador.atualizar_status(perfil.id, "Verificando...")

    credenciais_salvas = credenciais_mod.obter_credenciais(perfil.id)
    if credenciais_salvas:
        usuario_salvo, senha_salva = credenciais_salvas
        _preencher_e_submeter_login(driver, usuario_salvo, senha_salva)

    def monitorar():
        tempo_limite = time.time() + 300  # 5 min pra logar manualmente (ou confirmar login automático)
        logou = False
        sessao_morta = False
        usuario_capturado = ""
        senha_capturada = ""
        while time.time() < tempo_limite:
            try:
                # tela de login nativa da Kroton (usuário/senha)
                campos_usuario = driver.find_elements("css selector", config.SEL_CAMPO_USUARIO)
                for el in campos_usuario:
                    valor = (el.get_attribute("value") or "").strip()
                    if valor:
                        usuario_capturado = valor
                campos_senha = driver.find_elements("css selector", config.SEL_CAMPO_SENHA)
                for el in campos_senha:
                    valor = el.get_attribute("value") or ""
                    if valor:
                        senha_capturada = valor

                # fallback: tela de login Microsoft (SSO / Azure AD)
                elementos_email = driver.find_elements("css selector", config.SEL_CAMPO_EMAIL_LOGIN)
                for el in elementos_email:
                    valor = el.get_attribute("value")
                    if valor and "@" in valor:
                        gerenciador.atualizar_email_detectado(perfil.id, valor)

                # verifica se já saiu da tela de login (login concluído)
                if "login" not in driver.current_url:
                    gerenciador.atualizar_status(perfil.id, "Logado")
                    logou = True
                    break
            except WebDriverException as e:
                # Uma página com formulário tradicional (POST + reload completo,
                # como o login da Kroton) recarrega o documento inteiro ao
                # clicar "Entrar". Nesse instante é NORMAL o Selenium lançar
                # exceções passageiras (documento descarregando, contexto de
                # navegação trocando, etc.) — isso NÃO significa que a sessão
                # morreu. Só paramos de monitorar (e só aí fechamos o
                # navegador) se for um erro que realmente indica que o
                # processo do Chrome caiu; qualquer outra coisa é ignorada e
                # tentamos de novo no próximo ciclo, sem fechar nada.
                if sessao_esta_morta(e):
                    sessao_morta = True
                    break
            time.sleep(2)

        if logou:
            if usuario_capturado and senha_capturada:
                credenciais_mod.salvar_credenciais(perfil.id, usuario_capturado, senha_capturada)
                gerenciador.atualizar_apelido(perfil.id, usuario_capturado, personalizado=True)
            # dá um tempo pra Chrome gravar cookies/sessão em disco antes
            # de fechar e liberar a pasta do perfil pra outras operações.
            time.sleep(3)
        elif not sessao_morta:
            # nem logou nem a sessão morreu -> o tempo limite de 5 minutos
            # estourou esperando o usuário terminar o login manualmente.
            # Não fechamos silenciosamente: deixamos a janela aberta e só
            # atualizamos o status, pra não interromper alguém que ainda
            # está digitando.
            gerenciador.atualizar_status(perfil.id, "Não logado")
            return
        try:
            nav.fechar()
        except Exception:
            logger.exception("Falha ao fechar navegador de login manual do perfil %s", perfil.id)

    threading.Thread(target=monitorar, daemon=True).start()
    return nav


def garantir_login_para_execucao(driver, perfil: perfis_mod.Perfil) -> bool:
    """Chamado pelo runner ANTES de começar a processar CPFs. Garante que
    o perfil está logado — usando a sessão já persistida no perfil, ou
    (se necessário) logando automaticamente com as credenciais salvas.
    Nunca deixa o runner tentar buscar um CPF sem login confirmado antes
    (isso geraria erros em cascata desde o primeiro item).

    Retorna True se o login está confirmado. Retorna False (sem levantar
    exceção) se não há sessão válida nem credenciais salvas — quem chama
    deve pular esse perfil sem processar nenhum item."""
    driver.get(config.URL_HOME)
    if "login" not in driver.current_url:
        return True  # sessão já válida, nada a fazer

    credenciais_salvas = credenciais_mod.obter_credenciais(perfil.id)
    if not credenciais_salvas:
        logger.error(
            "Perfil %s sem sessão válida e sem credenciais salvas — é preciso fazer "
            "'Login manual' pelo menos uma vez antes de rodar uma execução.", perfil.apelido,
        )
        return False

    usuario, senha = credenciais_salvas
    driver.get(config.URL_LOGIN)
    if not _preencher_e_submeter_login(driver, usuario, senha):
        logger.error("Perfil %s: falha ao preencher/enviar o formulário de login automático.", perfil.apelido)
        return False

    if not _aguardar_redirecionamento_pos_login(driver):
        logger.error(
            "Perfil %s: login automático não confirmado (credenciais salvas podem estar "
            "desatualizadas — refaça o 'Login manual').", perfil.apelido,
        )
        return False

    return True


def verificar_login(perfil: perfis_mod.Perfil, gerenciador: perfis_mod.GerenciadorPerfis) -> bool:
    """Abre (headless) o perfil e verifica se a sessão ainda está válida.
    Recusa rodar se já existir um navegador aberto pra esse perfil (evita
    dois processos disputando a mesma pasta e um falso "Não logado")."""
    if perfil_tem_navegador_aberto(perfil.id):
        logger.warning(
            "Verificação de login adiada: já existe um navegador aberto para o perfil %s.", perfil.id
        )
        raise PerfilEmUsoError(
            f"Há uma janela de login aberta para o perfil '{perfil.apelido}'. "
            "Feche-a antes de verificar o login."
        )

    nav = NavegadorPerfil(perfil)
    try:
        driver = nav.abrir(headless=True)
        driver.get(config.URL_HOME)
        time.sleep(2)
        logado = "login" not in driver.current_url
        gerenciador.atualizar_status(perfil.id, "Logado" if logado else "Não logado")
        return logado
    except WebDriverException:
        gerenciador.atualizar_status(perfil.id, "Não logado")
        return False
    finally:
        nav.fechar()
