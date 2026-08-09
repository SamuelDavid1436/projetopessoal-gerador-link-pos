# -*- coding: utf-8 -*-
"""
crm_client.py
Toda a interação Selenium com a Plataforma Kroton (ERP):
  1. Busca o aluno pelo CPF na tela inicial.
  2. Clica na matrícula "Ativa" (ou "Pré-confirmada" se não houver Ativa).
  3. Abre o Extrato do Aluno e extrai dados pessoais.
  4. Percorre a paginação da tabela de lançamentos, coletando as parcelas
     de mensalidade (padrão "Xa. Parcela de Mensalidade MES/ANO (X/18)").
  5. Para as parcelas do mês anterior, vigente e seguinte que estejam
     "Em aberto", clica em "Gerar Link" e captura o link de pagamento.

Segue o mesmo padrão de robustez do projeto de referência: esperas
adaptativas (WebDriverWait), tratamento de elementos "stale", zoom
reduzido para grades largas, e retry em cliques.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException,
)

import config

logger = logging.getLogger("crm_client")


class ItemNaoEncontradoError(Exception):
    """Levantada quando o CPF não é localizado no sistema."""


@dataclass
class ParcelaMensalidade:
    id_linha: str
    mes: str
    ano: str
    parcela_num: str
    parcela_total: str
    mes_ano_ref: str          # "MES/ANO" como veio na tela
    ano_mes_ordenavel: str    # "YYYY-MM" pra comparação
    valor_pago: str
    situacao: str
    link_pagamento: str = ""


# ---------------------------------------------------------------------------
# Helpers de espera / retry robustos
# ---------------------------------------------------------------------------
def _clicar_com_retry(driver, elemento_ou_localizador, tentativas: int = 3, timeout: int = config.TIMEOUT_PADRAO):
    """Clica em um elemento, tolerando StaleElementReferenceException e
    ElementClickInterceptedException, tentando novamente com pequena espera."""
    ultimo_erro = None
    for _ in range(tentativas):
        try:
            if isinstance(elemento_ou_localizador, tuple):
                el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(elemento_ou_localizador))
            else:
                el = elemento_ou_localizador
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()
            return el
        except (StaleElementReferenceException, ElementClickInterceptedException) as e:
            ultimo_erro = e
            time.sleep(0.8)
        except TimeoutException as e:
            ultimo_erro = e
            time.sleep(0.5)
    raise ultimo_erro or TimeoutException("Falha ao clicar no elemento após múltiplas tentativas.")


def _aplicar_zoom_reduzido(driver):
    """Reduz o zoom da página quando a grade for larga/virtualizada, pra
    garantir que todas as colunas/linhas fiquem acessíveis ao Selenium."""
    try:
        driver.execute_script(f"document.body.style.zoom='{config.ZOOM_REDUZIDO}'")
    except WebDriverException:
        pass


def _restaurar_zoom(driver):
    try:
        driver.execute_script("document.body.style.zoom='100%'")
    except WebDriverException:
        pass


def _salvar_screenshot_erro(driver, identificador: str, tipo_erro: str):
    import os
    nome = f"{identificador}_{tipo_erro}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    caminho = os.path.join(config.DIR_SCREENSHOTS, nome)
    try:
        driver.save_screenshot(caminho)
    except WebDriverException:
        pass
    return caminho


# ---------------------------------------------------------------------------
# Passo 1: buscar aluno pelo CPF
# ---------------------------------------------------------------------------
def buscar_aluno_por_cpf(driver, cpf: str) -> Dict[str, str]:
    """Pesquisa o CPF no campo de busca, aguarda as opções aparecerem e
    clica na matrícula 'Ativa' (ou 'Pré-confirmada' se não houver Ativa).
    Retorna dict com data-id e data-ofertaid da opção escolhida."""
    driver.get(config.URL_HOME)

    campo = WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, config.SEL_CAMPO_BUSCA_MATRICULA))
    )
    campo.clear()
    campo.send_keys(cpf)

    try:
        WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config.SEL_DROPDOWN_OPCOES))
        )
    except TimeoutException:
        raise ItemNaoEncontradoError(config.MSG_NAO_ENCONTRADO)

    # espera adaptativa extra: aguarda a lista de opções estabilizar
    # (parar de crescer) antes de ler, já que carregam via AJAX
    opcoes = driver.find_elements(By.CSS_SELECTOR, config.SEL_DROPDOWN_OPCOES)
    qtd_anterior = -1
    tentativas_estabilizacao = 0
    while len(opcoes) != qtd_anterior and tentativas_estabilizacao < 10:
        qtd_anterior = len(opcoes)
        time.sleep(0.3)
        opcoes = driver.find_elements(By.CSS_SELECTOR, config.SEL_DROPDOWN_OPCOES)
        tentativas_estabilizacao += 1

    if not opcoes:
        raise ItemNaoEncontradoError(config.MSG_NAO_ENCONTRADO)

    opcao_escolhida = None
    opcao_preconfirmada = None
    for opcao in opcoes:
        nome_attr = (opcao.get_attribute("data-nome") or "").upper()
        if "SITUAÇÃO: ATIVA" in nome_attr or "SITUACAO: ATIVA" in nome_attr:
            opcao_escolhida = opcao
            break
        if "PRÉ-CONFIRMADA" in nome_attr or "PRE-CONFIRMADA" in nome_attr:
            if opcao_preconfirmada is None:
                opcao_preconfirmada = opcao

    if opcao_escolhida is None:
        opcao_escolhida = opcao_preconfirmada

    if opcao_escolhida is None:
        raise ItemNaoEncontradoError(config.MSG_NAO_ENCONTRADO)

    matricula_id = opcao_escolhida.get_attribute("data-id")
    oferta_id = opcao_escolhida.get_attribute("data-ofertaid")

    _clicar_com_retry(driver, opcao_escolhida)

    return {"matricula_id": matricula_id, "oferta_id": oferta_id}


# ---------------------------------------------------------------------------
# Passo 2: abrir extrato do aluno
# ---------------------------------------------------------------------------
def abrir_extrato_aluno(driver, matricula_id: str, oferta_id: str):
    """A partir da tela de dados pessoais (matricula/show), clica em
    'Visualizar Extrato do Aluno'."""
    try:
        WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
            EC.url_contains("matricula/show")
        )
    except TimeoutException:
        pass  # segue tentando localizar o botão mesmo assim

    try:
        botao_extrato = WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, config.SEL_BOTAO_EXTRATO_ALUNO))
        )
        _clicar_com_retry(driver, botao_extrato)
    except TimeoutException:
        # fallback: navega direto pela URL, já que o padrão é conhecido
        url_extrato = (
            f"{config.URL_EXTRATO_BASE}?matriculaId={matricula_id}"
            f"&max={config.MAX_POR_PAGINA_EXTRATO}&offset=0"
        )
        driver.get(url_extrato)

    WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, config.SEL_TABELA_EXTRATO))
    )


# ---------------------------------------------------------------------------
# Passo 3: extrair dados pessoais
# ---------------------------------------------------------------------------
def extrair_dados_pessoais(driver) -> Dict[str, str]:
    """Extrai Nome, Situação, Curso, Plano, CPF e Email do bloco de dados
    pessoais exibido junto ao extrato."""
    dados = {"Nome": "", "Situacao_Matricula": "", "Curso": "", "Plano": "", "CPF": "", "Email": ""}

    try:
        texto_pagina = WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
            lambda d: d.find_element(By.TAG_NAME, "body")
        ).text
    except TimeoutException:
        return dados

    padroes = {
        "Nome": r"Nome:\s*(.+?)(?:\n|$)",
        "Situacao_Matricula": r"Situa[cç][aã]o:\s*(.+?)(?:\n|$)",
        "Curso": r"Curso:\s*(.+?)(?:\n|$)",
        "Plano": r"Plano:\s*(.+?)(?:\n|$)",
        "CPF": r"CPF:\s*([\d.\-]+)",
        "Email": r"E-?mail:\s*([\w\.\-\+]+@[\w\.\-]+)",
    }

    for campo, padrao in padroes.items():
        m = re.search(padrao, texto_pagina, flags=re.IGNORECASE)
        if m:
            dados[campo] = m.group(1).strip()

    return dados


# ---------------------------------------------------------------------------
# Passo 4: percorrer paginação e coletar parcelas de mensalidade
# ---------------------------------------------------------------------------
def _mes_ano_para_ordenavel(nome_mes: str, ano: str) -> str:
    numero_mes = config.MESES_PT.get(nome_mes.upper(), 0)
    return f"{ano}-{numero_mes:02d}"


def _extrair_id_linha(linha) -> str:
    """Extrai o ID da linha de forma robusta. O atributo 'data-id' fica no
    <td> (não no <tr> — esse foi um bug real já corrigido aqui), então
    tentamos o <td data-id> primeiro e caímos pro href do link
    'Visualizar'/'Gerar Link' (padrão .../show/<id>) como reforço, já que
    ambos os links sempre apontam pro mesmo ID da linha."""
    try:
        td_id = linha.find_element(By.CSS_SELECTOR, "td[data-id]")
        valor = (td_id.get_attribute("data-id") or "").strip()
        if valor:
            return valor
    except (NoSuchElementException, StaleElementReferenceException):
        pass

    try:
        link = linha.find_element(By.CSS_SELECTOR, "a[href*='/show/']")
        href = link.get_attribute("href") or ""
        m = re.search(r"/show/(\d+)", href)
        if m:
            return m.group(1)
    except (NoSuchElementException, StaleElementReferenceException):
        pass

    return ""


def _extrair_parcelas_da_pagina(driver) -> List[ParcelaMensalidade]:
    parcelas = []
    linhas = driver.find_elements(By.CSS_SELECTOR, config.SEL_LINHAS_TABELA)

    for linha in linhas:
        try:
            descricao_el = linha.find_element(By.CSS_SELECTOR, "td[data-descricao]")
            descricao = descricao_el.get_attribute("data-descricao") or ""
        except NoSuchElementException:
            continue

        m = re.search(config.REGEX_PARCELA_MENSALIDADE, descricao, flags=re.IGNORECASE | re.UNICODE)
        if not m:
            continue  # só nos interessam as parcelas de mensalidade

        mes, ano, parcela_num, parcela_total = m.groups()

        id_linha = _extrair_id_linha(linha)

        try:
            situacao_el = linha.find_element(By.CSS_SELECTOR, "td[data-situacao]")
            situacao = situacao_el.get_attribute("data-situacao") or ""
            valor_pago_tds = linha.find_elements(By.TAG_NAME, "td")
            # "Valor Pago" é a coluna logo após "Valor" na tabela (índice 8 na estrutura descrita)
            valor_pago = ""
            if len(valor_pago_tds) >= 9:
                valor_pago = valor_pago_tds[8].text.strip()
        except (NoSuchElementException, StaleElementReferenceException):
            situacao, valor_pago = "", ""

        parcelas.append(
            ParcelaMensalidade(
                id_linha=id_linha,
                mes=mes,
                ano=ano,
                parcela_num=parcela_num,
                parcela_total=parcela_total,
                mes_ano_ref=f"{mes}/{ano}",
                ano_mes_ordenavel=_mes_ano_para_ordenavel(mes, ano),
                valor_pago=valor_pago,
                situacao=situacao,
            )
        )

    return parcelas


def coletar_todas_parcelas(driver, matricula_id: str) -> List[ParcelaMensalidade]:
    """Percorre todas as páginas da tabela de extrato (paginação por
    offset) coletando as parcelas de mensalidade."""
    todas_parcelas: List[ParcelaMensalidade] = []
    offset = 0

    _aplicar_zoom_reduzido(driver)
    try:
        while True:
            url_pagina = (
                f"{config.URL_EXTRATO_BASE}?matriculaId={matricula_id}"
                f"&max={config.MAX_POR_PAGINA_EXTRATO}&offset={offset}"
            )
            driver.get(url_pagina)

            try:
                WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config.SEL_TABELA_EXTRATO))
                )
            except TimeoutException:
                break

            parcelas_pagina = _extrair_parcelas_da_pagina(driver)
            todas_parcelas.extend(parcelas_pagina)

            # verifica se existe próxima página observando os links de paginação
            links_paginacao = driver.find_elements(By.CSS_SELECTOR, config.SEL_PAGINACAO)
            offsets_disponiveis = set()
            for link in links_paginacao:
                href = link.get_attribute("href") or ""
                m = re.search(r"offset=(\d+)", href)
                if m:
                    offsets_disponiveis.add(int(m.group(1)))

            proximo_offset = offset + config.MAX_POR_PAGINA_EXTRATO
            if proximo_offset in offsets_disponiveis:
                offset = proximo_offset
            else:
                break
    finally:
        _restaurar_zoom(driver)

    return todas_parcelas


# ---------------------------------------------------------------------------
# Passo 5: gerar link de pagamento para as parcelas elegíveis
# ---------------------------------------------------------------------------
def _mes_atual_ordenavel() -> str:
    agora = datetime.now()
    return f"{agora.year}-{agora.month:02d}"


def _meses_elegiveis() -> set:
    """Retorna o conjunto {mês anterior, mês vigente, mês seguinte} no
    formato 'YYYY-MM'."""
    agora = datetime.now()
    meses = set()
    for delta in (-1, 0, 1):
        mes = agora.month + delta
        ano = agora.year
        if mes < 1:
            mes += 12
            ano -= 1
        elif mes > 12:
            mes -= 12
            ano += 1
        meses.add(f"{ano}-{mes:02d}")
    return meses


def selecionar_parcelas_para_link(parcelas: List[ParcelaMensalidade]) -> List[ParcelaMensalidade]:
    """Filtra só as parcelas do mês anterior/vigente/seguinte que estejam
    'Em aberto'. Parcelas 'Concluído' nunca geram link."""
    elegiveis = _meses_elegiveis()
    return [
        p for p in parcelas
        if p.ano_mes_ordenavel in elegiveis
        and p.situacao.strip().lower() == config.SITUACAO_ELEGIVEL_LINK.lower()
    ]


def gerar_link_pagamento(driver, matricula_id: str, id_linha: str) -> str:
    """Navega até a página de detalhe da parcela ('Gerar Link'), aguarda o
    input do link de pagamento e retorna o valor."""
    if not id_linha:
        # Guarda de segurança: nunca navegar com ID vazio (evita repetir o
        # bug de URL quebrada .../show/ sem ID, já corrigido na extração).
        logger.warning("id_linha vazio — geração de link pulada para evitar URL inválida.")
        return ""

    url_detalhe = f"{config.URL_EXTRATO_BASE.rsplit('/', 1)[0]}/show/{id_linha}"
    driver.get(url_detalhe)

    try:
        campo_link = WebDriverWait(driver, config.TIMEOUT_PADRAO).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config.SEL_INPUT_LINK_PAGAMENTO))
        )
    except TimeoutException:
        return ""

    for _ in range(3):
        valor = campo_link.get_attribute("value")
        if valor:
            return valor.strip()
        time.sleep(0.5)
        try:
            campo_link = driver.find_element(By.CSS_SELECTOR, config.SEL_INPUT_LINK_PAGAMENTO)
        except (NoSuchElementException, StaleElementReferenceException):
            break

    return ""


# ---------------------------------------------------------------------------
# Orquestração do item completo (usada pelo runner.py)
# ---------------------------------------------------------------------------
def processar_cpf(driver, cpf: str) -> List[Dict]:
    """Processa um CPF do início ao fim e retorna uma lista de linhas
    (uma por parcela relevante) prontas pra gravação na planilha de saída.
    Levanta ItemNaoEncontradoError se o CPF não for localizado."""
    resultado = buscar_aluno_por_cpf(driver, cpf)
    abrir_extrato_aluno(driver, resultado["matricula_id"], resultado["oferta_id"])
    dados_pessoais = extrair_dados_pessoais(driver)

    parcelas = coletar_todas_parcelas(driver, resultado["matricula_id"])
    parcelas_para_link = selecionar_parcelas_para_link(parcelas)

    # Itera diretamente sobre os objetos elegíveis (que são as mesmas
    # instâncias presentes em `parcelas`) — evita comparar por id_linha,
    # o que poderia agrupar erroneamente linhas com ID vazio/repetido.
    for parcela in parcelas_para_link:
        parcela.link_pagamento = gerar_link_pagamento(driver, resultado["matricula_id"], parcela.id_linha)

    linhas = []
    for parcela in parcelas:
        linha = {
            "CPF": cpf,
            "Nome": dados_pessoais.get("Nome", ""),
            "Situacao_Matricula": dados_pessoais.get("Situacao_Matricula", ""),
            "Curso": dados_pessoais.get("Curso", ""),
            "Plano": dados_pessoais.get("Plano", ""),
            "Email": dados_pessoais.get("Email", ""),
            "Mes_Ano": parcela.mes_ano_ref,
            "Valor_Pago": parcela.valor_pago,
            "Situacao_Parcela": parcela.situacao,
            "Link_Pagamento": parcela.link_pagamento,
            "Status_Processamento": "Sucesso",
            "Observacao": "" if (dados_pessoais.get("Nome") and dados_pessoais.get("Email")) else "Aviso: campos pessoais vazios",
        }
        linhas.append(linha)

    if not linhas:
        # aluno encontrado, mas sem nenhuma parcela de mensalidade -> trava de qualidade
        linhas.append({
            "CPF": cpf,
            "Nome": dados_pessoais.get("Nome", ""),
            "Situacao_Matricula": dados_pessoais.get("Situacao_Matricula", ""),
            "Curso": dados_pessoais.get("Curso", ""),
            "Plano": dados_pessoais.get("Plano", ""),
            "Email": dados_pessoais.get("Email", ""),
            "Mes_Ano": "",
            "Valor_Pago": "",
            "Situacao_Parcela": "",
            "Link_Pagamento": "",
            "Status_Processamento": "Sucesso",
            "Observacao": "Aviso: nenhuma parcela de mensalidade encontrada no extrato",
        })

    return linhas
