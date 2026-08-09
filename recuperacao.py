# -*- coding: utf-8 -*-
"""
recuperacao.py
Log de retomada: grava progresso parcial a cada item processado, pra poder
oferecer recuperação se o programa cair no meio de uma execução.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import config


class LogRecuperacao:
    def __init__(self, caminho_arquivo: str = config.ARQ_RECUPERACAO):
        self.caminho_arquivo = caminho_arquivo

    def existe_pendente(self) -> bool:
        return os.path.exists(self.caminho_arquivo)

    def carregar(self) -> Optional[Dict]:
        if not self.existe_pendente():
            return None
        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, TypeError):
            return None

    def iniciar(self, exec_id: str, pasta_saida: str, itens_totais: int):
        estado = {
            "exec_id": exec_id,
            "pasta_saida": pasta_saida,
            "itens_totais": itens_totais,
            "resultados_parciais": [],
            "atualizado_em": datetime.now().isoformat(timespec="seconds"),
        }
        self._gravar(estado)

    def registrar_resultado(self, resultado: Dict):
        estado = self.carregar()
        if estado is None:
            return
        estado["resultados_parciais"].append(resultado)
        estado["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
        self._gravar(estado)

    def limpar(self):
        if os.path.exists(self.caminho_arquivo):
            os.remove(self.caminho_arquivo)

    def _gravar(self, estado: Dict):
        with open(self.caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
