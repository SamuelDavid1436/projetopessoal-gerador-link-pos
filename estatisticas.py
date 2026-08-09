# -*- coding: utf-8 -*-
"""
estatisticas.py
Contador persistente de "Dados Capturados (histórico total)", independente
do histórico de execuções (que pode ser filtrado/exibido parcialmente).
Também expõe o cálculo de "Execuções Hoje" e "Tempo Total Hoje" a partir
do histórico de execuções (esses dois já "zeram" sozinhos a cada dia,
por serem calculados por data).
"""

import json
import os
from datetime import datetime, date
from typing import Dict

import config


class Estatisticas:
    def __init__(self, caminho_arquivo: str = config.ARQ_ESTATISTICAS):
        self.caminho_arquivo = caminho_arquivo
        self.dados: Dict = {"total_capturados": 0}
        self._carregar()

    def _carregar(self):
        if os.path.exists(self.caminho_arquivo):
            try:
                with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                    self.dados = json.load(f)
            except (json.JSONDecodeError, TypeError):
                pass

    def _salvar(self):
        with open(self.caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(self.dados, f, ensure_ascii=False, indent=2)

    def registrar_capturados(self, quantidade: int):
        """Soma ao total histórico — nunca diminui sozinho, só via zerar()."""
        self.dados["total_capturados"] = self.dados.get("total_capturados", 0) + quantidade
        self._salvar()

    def total_capturados(self) -> int:
        return self.dados.get("total_capturados", 0)

    def zerar(self):
        self.dados["total_capturados"] = 0
        self._salvar()


# ---------------------------------------------------------------------------
# Métricas derivadas do histórico de execuções (naturalmente "zeram" por dia)
# ---------------------------------------------------------------------------
def _data_registro(registro: Dict) -> date:
    try:
        return datetime.fromisoformat(registro["inicio"]).date()
    except (KeyError, ValueError, TypeError):
        return date.min


def execucoes_hoje(registros) -> int:
    hoje = date.today()
    return sum(1 for r in registros if _data_registro(r) == hoje)


def tempo_total_hoje_segundos(registros) -> int:
    hoje = date.today()
    total = 0
    for r in registros:
        if _data_registro(r) != hoje:
            continue
        total += duracao_segundos(r)
    return total


def duracao_segundos(registro: Dict) -> int:
    try:
        inicio = datetime.fromisoformat(registro["inicio"])
    except (KeyError, ValueError, TypeError):
        return 0
    if registro.get("fim"):
        try:
            fim = datetime.fromisoformat(registro["fim"])
        except (ValueError, TypeError):
            fim = datetime.now()
    else:
        fim = datetime.now()
    return max(0, int((fim - inicio).total_seconds()))


def formatar_duracao(segundos: int) -> str:
    h, resto = divmod(max(0, int(segundos)), 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
