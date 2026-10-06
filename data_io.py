# -*- coding: utf-8 -*-
"""
data_io.py
Leitura da base de entrada (CSV/Excel, com ou sem cabeçalho) e gravação dos
resultados (CSV ; utf-8-sig + XLSX), uma pasta por execução.
"""

import csv
import os
import re
from datetime import datetime
from typing import List, Dict

import pandas as pd

import config


# ---------------------------------------------------------------------------
# Leitura da base de entrada
# ---------------------------------------------------------------------------
def _detectar_separador_csv(caminho: str, encoding: str = "utf-8-sig") -> str:
    """Detecta separador de forma confiável usando csv.Sniffer sobre uma
    amostra do arquivo. NÃO usa sep=None do pandas puro (isso trunca valores
    numéricos em arquivos sem cabeçalho)."""
    with open(caminho, "r", encoding=encoding, errors="ignore") as f:
        amostra = f.read(4096)
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=";,|\t")
        return dialeto.delimiter
    except csv.Error:
        # fallback: conta ocorrências dos candidatos mais comuns
        candidatos = [";", ",", "\t", "|"]
        contagens = {c: amostra.count(c) for c in candidatos}
        return max(contagens, key=contagens.get) if any(contagens.values()) else ","


def _tem_cabecalho(primeira_linha_valores: List[str]) -> bool:
    """Heurística simples: se a primeira linha contém algo parecido com um
    CPF (11 dígitos, com ou sem pontuação), tratamos como dado, não cabeçalho."""
    for valor in primeira_linha_valores:
        digitos = re.sub(r"\D", "", str(valor))
        if len(digitos) == 11:
            return False
    return True


def ler_base_entrada(caminho: str) -> pd.DataFrame:
    """Lê CSV ou Excel, com ou sem cabeçalho, detectando o separador de
    forma confiável. Retorna DataFrame com pelo menos a coluna 'CPF'."""
    extensao = os.path.splitext(caminho)[1].lower()

    if extensao in (".xlsx", ".xls", ".xlsm"):
        df_bruto = pd.read_excel(caminho, header=None, dtype=str)
        primeira_linha = df_bruto.iloc[0].fillna("").tolist()
        tem_cab = _tem_cabecalho(primeira_linha)
        df = pd.read_excel(caminho, header=0 if tem_cab else None, dtype=str)
    else:
        separador = _detectar_separador_csv(caminho)
        df_bruto = pd.read_csv(
            caminho, sep=separador, header=None, dtype=str, nrows=1, engine="python"
        )
        primeira_linha = df_bruto.iloc[0].fillna("").tolist()
        tem_cab = _tem_cabecalho(primeira_linha)
        df = pd.read_csv(
            caminho,
            sep=separador,
            header=0 if tem_cab else None,
            dtype=str,
            engine="python",
            encoding="utf-8-sig",
        )

    if not tem_cab:
        # renomeia colunas genericamente e assume a primeira como CPF e a
        # segunda (se houver) como telefone
        df.columns = [f"col_{i}" for i in range(len(df.columns))]
        df = df.rename(columns={"col_0": "CPF"})
        if "col_1" in df.columns:
            df = df.rename(columns={"col_1": "Telefone"})
    else:
        # normaliza nome da coluna de CPF, tolerando variações
        for col in df.columns:
            if re.sub(r"[^A-Za-z]", "", str(col)).upper() == "CPF":
                df = df.rename(columns={col: "CPF"})
                break
        # coluna de telefone (opcional): Telefone, Celular, Fone ou WhatsApp
        for col in df.columns:
            if col == "CPF":
                continue
            nome = re.sub(r"[^A-Za-z]", "", str(col)).upper()
            if nome in config.NOMES_COLUNA_TELEFONE:
                df = df.rename(columns={col: "Telefone"})
                break

    if "CPF" not in df.columns:
        raise ValueError("Não foi possível identificar a coluna de CPF na base de entrada.")

    df["CPF"] = df["CPF"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(11)
    df = df[df["CPF"].str.len() == 11].reset_index(drop=True)

    if "Telefone" in df.columns:
        df["Telefone"] = df["Telefone"].fillna("").astype(str).str.strip()
        df.loc[df["Telefone"].str.lower() == "nan", "Telefone"] = ""
    else:
        df["Telefone"] = ""
    return df


def mapa_telefones(df: pd.DataFrame) -> Dict[str, str]:
    """CPF -> telefone informado na base (só os que vieram preenchidos).
    Se o CPF se repetir, vale o primeiro telefone preenchido."""
    mapa: Dict[str, str] = {}
    for cpf, tel in zip(df["CPF"], df.get("Telefone", [""] * len(df))):
        if tel and cpf not in mapa:
            mapa[cpf] = tel
    return mapa


def formatar_telefone_disparo(telefone: str) -> str:
    """Formata no padrão de disparo: 55 + DDD + número, só dígitos.
    Retorna '' se o número não tiver tamanho de telefone brasileiro."""
    digitos = re.sub(r"\D", "", str(telefone or ""))
    digitos = digitos.lstrip("0")
    if digitos.startswith("55") and len(digitos) in (12, 13):
        return digitos
    if len(digitos) in (10, 11):
        return "55" + digitos
    return ""


# ---------------------------------------------------------------------------
# Gravação dos resultados
# ---------------------------------------------------------------------------
def criar_pasta_saida() -> str:
    """Cada execução gera sua própria pasta, nomeada com data/hora — nunca
    mistura execuções diferentes."""
    nome = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pasta = os.path.join(config.DIR_SAIDA, nome)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def gravar_resultados(
    pasta_saida: str, linhas: List[Dict], nome_base: str = "resultado", colunas: List[str] = None,
    rotulos: Dict[str, str] = None,
) -> Dict[str, str]:
    """Grava CSV (';', utf-8-sig) + XLSX. Se `colunas` não for informado,
    usa o conjunto fixo de colunas do formato longo (config.COLUNAS_SAIDA).
    `rotulos` troca o nome interno da coluna pelo texto do cabeçalho."""
    df = pd.DataFrame(linhas, columns=colunas or config.COLUNAS_SAIDA)
    if rotulos:
        df = df.rename(columns=rotulos)

    caminho_csv = os.path.join(pasta_saida, f"{nome_base}.csv")
    caminho_xlsx = os.path.join(pasta_saida, f"{nome_base}.xlsx")

    df.to_csv(caminho_csv, sep=";", index=False, encoding="utf-8-sig")
    df.to_excel(caminho_xlsx, index=False)

    return {"csv": caminho_csv, "xlsx": caminho_xlsx}


def gerar_base_reprocessamento(pasta_saida: str, linhas: List[Dict]) -> str:
    """Gera uma base nova só com os itens que deram erro, pronta pra
    reimportar (só a coluna CPF, que é o que a base de entrada exige)."""
    erros = [l for l in linhas if l.get("Status_Processamento") == "Erro"]
    df = pd.DataFrame({"CPF": [l["CPF"] for l in erros]})
    caminho = os.path.join(pasta_saida, "reprocessar_erros.xlsx")
    df.to_excel(caminho, index=False)
    return caminho


# ---------------------------------------------------------------------------
# Pivô: formato "longo" (uma linha por parcela) -> "largo" (uma linha por
# CPF, com colunas FIXAS por mês do calendário: Junho a Dezembro/2026)
# ---------------------------------------------------------------------------
def _nome_mes(mes_ano: str) -> "tuple[str, int]":
    """'OUTUBRO/2026' -> ('Outubro', 2026). Retorna ('', 0) se inválido."""
    mes_nome, _, ano_str = (mes_ano or "").strip().partition("/")
    try:
        return mes_nome.strip().capitalize(), int(ano_str.strip())
    except ValueError:
        return "", 0


def pivotar_para_wide(linhas: List[Dict]) -> "tuple[List[Dict], List[str]]":
    """Transforma o resultado 'longo' (uma linha por parcela) em 'largo'
    (uma linha por aluno/CPF), com colunas FIXAS por mês do calendário —
    sempre 'Junho', 'Julho', ... 'Dezembro' (config.MESES_SAIDA_ORDENADOS,
    ano config.ANO_SAIDA), na mesma posição em toda linha.

    Ordem das colunas: Nome, CPF, Telefone, Situação -> para cada mês
    '{Mês} - Situação Mensalidade' (situação da parcela na plataforma, ou
    'Sem mensalidade'), '{Mês} - Valor Pago', '{Mês} - Vencimento' e
    '{Mês} - Link Pagamento' -> Curso, Plano, E-mail, Status, Observação.
    Competências fora da janela são ignoradas aqui (ficam no detalhado)."""
    grupos: Dict[str, Dict] = {}
    ordem_cpfs: List[str] = []

    for linha in linhas:
        cpf = linha.get("CPF", "")
        if cpf not in grupos:
            grupos[cpf] = {
                "base": {col: linha.get(col, "") for col in config.COLUNAS_BASE_SAIDA_LARGA},
                "por_mes": {},
            }
            grupos[cpf]["base"]["CPF"] = cpf
            ordem_cpfs.append(cpf)
        else:
            base = grupos[cpf]["base"]
            if not base.get("Telefone") and linha.get("Telefone"):
                base["Telefone"] = linha.get("Telefone")
            # se qualquer linha desse CPF for erro, o aluno inteiro fica marcado como erro
            if linha.get("Status_Processamento") == "Erro":
                base["Status_Processamento"] = "Erro"
                nova_obs = (linha.get("Observacao") or "").strip()
                if nova_obs and nova_obs not in base.get("Observacao", ""):
                    base["Observacao"] = (base.get("Observacao", "") + " | " + nova_obs).strip(" |")

        mes_nome, ano_int = _nome_mes(linha.get("Mes_Ano"))
        if not mes_nome:
            continue  # linha sem competência (ex.: erro, ou aviso sem parcela)
        if ano_int != config.ANO_SAIDA or mes_nome not in config.MESES_SAIDA_ORDENADOS:
            continue

        grupos[cpf]["por_mes"][mes_nome] = {
            "situacao": (linha.get("Situacao_Parcela") or "").strip() or config.TEXTO_COM_MENSALIDADE,
            "valor_pago": linha.get("Valor_Pago", ""),
            "vencimento": linha.get("Vencimento", ""),
            "link_pagamento": linha.get("Link_Pagamento", ""),
        }

    sufixos = [
        ("situacao", config.SUFIXO_MES_SITUACAO),
        ("valor_pago", config.SUFIXO_MES_VALOR),
        ("vencimento", config.SUFIXO_MES_VENCIMENTO),
        ("link_pagamento", config.SUFIXO_MES_LINK),
    ]
    colunas_dinamicas: List[str] = []
    for mes in config.MESES_SAIDA_ORDENADOS:
        colunas_dinamicas += [f"{mes} - {sufixo}" for _, sufixo in sufixos]

    linhas_largas = []
    for cpf in ordem_cpfs:
        grupo = grupos[cpf]
        linha_larga = dict(grupo["base"])
        for mes in config.MESES_SAIDA_ORDENADOS:
            dados_mes = grupo["por_mes"].get(mes)
            for chave, sufixo in sufixos:
                if dados_mes:
                    linha_larga[f"{mes} - {sufixo}"] = dados_mes[chave]
                else:
                    linha_larga[f"{mes} - {sufixo}"] = (
                        config.TEXTO_SEM_MENSALIDADE if chave == "situacao" else ""
                    )
        linhas_largas.append(linha_larga)

    colunas = config.COLUNAS_INICIO_SAIDA_LARGA + colunas_dinamicas + config.COLUNAS_FIM_SAIDA_LARGA
    return linhas_largas, colunas


# ---------------------------------------------------------------------------
# Base de disparo: uma linha por aluno com link de pagamento gerado
# ---------------------------------------------------------------------------
def _prioridade_disparo(linha: Dict, hoje: datetime) -> "tuple":
    """Quanto menor, melhor. Prioriza a parcela do mês atual; sem link no
    mês atual, a do mês mais próximo (o anterior vem antes do seguinte)."""
    mes_nome, ano = _nome_mes(linha.get("Mes_Ano"))
    numero = config.MESES_PT.get(mes_nome.upper(), 0)
    distancia = (ano * 12 + numero) - (hoje.year * 12 + hoje.month)
    return (abs(distancia), 0 if distancia <= 0 else 1)


def montar_base_disparo(linhas: List[Dict], hoje: datetime = None) -> "tuple[List[Dict], List[str]]":
    """Uma linha por aluno, com o link da parcela do mês atual (ou, se o mês
    atual não tiver link, do mês mais próximo — o anterior antes do
    seguinte). Alunos sem nenhum link gerado ficam de fora.
    Colunas: CPF, Nome, Telefone (55 + DDD + número), MÊS, Vencimento e
    '{Mês} - Link Pagamento' (ou só 'Link Pagamento' se a base tiver
    alunos com meses diferentes)."""
    hoje = hoje or datetime.now()
    escolhidas: Dict[str, Dict] = {}
    telefones: Dict[str, str] = {}
    ordem: List[str] = []

    for linha in linhas:
        cpf = linha.get("CPF", "")
        if cpf not in ordem:
            ordem.append(cpf)
        if linha.get("Telefone") and not telefones.get(cpf):
            telefones[cpf] = linha["Telefone"]
        if not (linha.get("Link_Pagamento") or "").strip():
            continue
        atual = escolhidas.get(cpf)
        if atual is None or _prioridade_disparo(linha, hoje) < _prioridade_disparo(atual, hoje):
            escolhidas[cpf] = linha

    linhas_disparo = []
    for cpf in ordem:
        linha = escolhidas.get(cpf)
        if not linha:
            continue
        mes_nome, _ = _nome_mes(linha.get("Mes_Ano"))
        linhas_disparo.append({
            "CPF": cpf,
            "Nome": linha.get("Nome", ""),
            "Telefone": formatar_telefone_disparo(telefones.get(cpf, "")),
            config.COLUNA_DISPARO_MES: mes_nome,
            "Vencimento": linha.get("Vencimento", ""),
            "_link": linha.get("Link_Pagamento", "").strip(),
        })

    meses = {l[config.COLUNA_DISPARO_MES] for l in linhas_disparo}
    coluna_link = (
        f"{meses.pop()} - {config.SUFIXO_MES_LINK}" if len(meses) == 1
        else config.COLUNA_DISPARO_LINK_GENERICA
    )
    for l in linhas_disparo:
        l[coluna_link] = l.pop("_link")

    colunas = ["CPF", "Nome", "Telefone", config.COLUNA_DISPARO_MES, "Vencimento", coluna_link]
    return linhas_disparo, colunas


def gravar_saidas_execucao(pasta_saida: str, linhas: List[Dict], sufixo: str = "") -> Dict[str, str]:
    """Grava todos os arquivos de uma execução (CSV + XLSX cada):
    resultado, resultado_detalhado e base_disparo. `sufixo` é usado na
    recuperação ('_recuperado')."""
    linhas_largas, colunas_largas = pivotar_para_wide(linhas)
    gravar_resultados(pasta_saida, linhas_largas, nome_base=f"resultado{sufixo}",
                      colunas=colunas_largas, rotulos=config.ROTULOS_COLUNAS)
    gravar_resultados(pasta_saida, linhas, nome_base=f"resultado{sufixo}_detalhado")
    linhas_disparo, colunas_disparo = montar_base_disparo(linhas)
    gravar_resultados(pasta_saida, linhas_disparo, nome_base=f"base_disparo{sufixo}",
                      colunas=colunas_disparo, rotulos=config.ROTULOS_COLUNAS)
    return {"linhas_largas": linhas_largas}
