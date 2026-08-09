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
        # renomeia colunas genericamente e assume a primeira como CPF
        df.columns = [f"col_{i}" for i in range(len(df.columns))]
        df = df.rename(columns={"col_0": "CPF"})
    else:
        # normaliza nome da coluna de CPF, tolerando variações
        for col in df.columns:
            if re.sub(r"[^A-Za-z]", "", str(col)).upper() == "CPF":
                df = df.rename(columns={col: "CPF"})
                break

    if "CPF" not in df.columns:
        raise ValueError("Não foi possível identificar a coluna de CPF na base de entrada.")

    df["CPF"] = df["CPF"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(11)
    df = df[df["CPF"].str.len() == 11].reset_index(drop=True)
    return df


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
    pasta_saida: str, linhas: List[Dict], nome_base: str = "resultado", colunas: List[str] = None
) -> Dict[str, str]:
    """Grava CSV (';', utf-8-sig) + XLSX. Se `colunas` não for informado,
    usa o conjunto fixo de colunas do formato longo (config.COLUNAS_SAIDA)."""
    df = pd.DataFrame(linhas, columns=colunas or config.COLUNAS_SAIDA)

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
def pivotar_para_wide(linhas: List[Dict]) -> "tuple[List[Dict], List[str]]":
    """Transforma o resultado 'longo' (uma linha por parcela) em 'largo'
    (uma linha por aluno/CPF), com colunas FIXAS por mês do calendário —
    sempre 'Junho', 'Julho', ... 'Dezembro' (config.MESES_SAIDA_ORDENADOS,
    ano config.ANO_SAIDA), na mesma posição em toda linha, pra dar pra
    comparar entre alunos diretamente.

    Cada mês vira 3 colunas: '{Mes} - Situação' (Com/Sem mensalidade),
    '{Mes} - Valor Pago' e '{Mes} - Link Pagamento'. Competências fora da
    janela Junho-Dezembro do ano configurado são ignoradas — não entram no
    arquivo de saída largo (mas continuam no detalhado)."""
    grupos: Dict[str, Dict] = {}
    ordem_cpfs: List[str] = []

    for linha in linhas:
        cpf = linha.get("CPF", "")
        if cpf not in grupos:
            grupos[cpf] = {
                "base": {
                    "CPF": cpf,
                    "Nome": linha.get("Nome", ""),
                    "Situacao_Matricula": linha.get("Situacao_Matricula", ""),
                    "Curso": linha.get("Curso", ""),
                    "Plano": linha.get("Plano", ""),
                    "Email": linha.get("Email", ""),
                    "Status_Processamento": linha.get("Status_Processamento", ""),
                    "Observacao": linha.get("Observacao", ""),
                },
                "por_mes": {},  # nome do mês -> {"valor_pago":..., "link_pagamento":...}
            }
            ordem_cpfs.append(cpf)
        else:
            # se qualquer linha desse CPF for erro, o aluno inteiro fica marcado como erro
            if linha.get("Status_Processamento") == "Erro":
                base = grupos[cpf]["base"]
                base["Status_Processamento"] = "Erro"
                nova_obs = (linha.get("Observacao") or "").strip()
                if nova_obs and nova_obs not in base.get("Observacao", ""):
                    base["Observacao"] = (base.get("Observacao", "") + " | " + nova_obs).strip(" |")

        mes_ano = (linha.get("Mes_Ano") or "").strip()
        if not mes_ano or "/" not in mes_ano:
            continue  # linha sem competência (ex.: erro, ou aviso sem parcela)

        mes_nome, _, ano_str = mes_ano.partition("/")
        mes_nome_cap = mes_nome.strip().capitalize()
        try:
            ano_int = int(ano_str.strip())
        except ValueError:
            continue

        # só entra na janela fixa Junho-Dezembro do ano configurado
        if ano_int != config.ANO_SAIDA or mes_nome_cap not in config.MESES_SAIDA_ORDENADOS:
            continue

        grupos[cpf]["por_mes"][mes_nome_cap] = {
            "valor_pago": linha.get("Valor_Pago", ""),
            "link_pagamento": linha.get("Link_Pagamento", ""),
        }

    colunas_dinamicas: List[str] = []
    for mes in config.MESES_SAIDA_ORDENADOS:
        colunas_dinamicas += [f"{mes} - Situação", f"{mes} - Valor Pago", f"{mes} - Link Pagamento"]

    linhas_largas = []
    for cpf in ordem_cpfs:
        grupo = grupos[cpf]
        linha_larga = dict(grupo["base"])
        for mes in config.MESES_SAIDA_ORDENADOS:
            dados_mes = grupo["por_mes"].get(mes)
            if dados_mes:
                linha_larga[f"{mes} - Situação"] = config.TEXTO_COM_MENSALIDADE
                linha_larga[f"{mes} - Valor Pago"] = dados_mes["valor_pago"]
                linha_larga[f"{mes} - Link Pagamento"] = dados_mes["link_pagamento"]
            else:
                linha_larga[f"{mes} - Situação"] = config.TEXTO_SEM_MENSALIDADE
                linha_larga[f"{mes} - Valor Pago"] = ""
                linha_larga[f"{mes} - Link Pagamento"] = ""
        linhas_largas.append(linha_larga)

    colunas = config.COLUNAS_BASE_SAIDA_LARGA + colunas_dinamicas
    return linhas_largas, colunas
