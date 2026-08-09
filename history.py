# -*- coding: utf-8 -*-
"""
history.py
Histórico de execuções: cada execução vira um registro com pasta de saída,
totais e status geral, pra alimentar a tela de Execuções.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

import config


class Historico:
    def __init__(self, caminho_arquivo: str = config.ARQ_HISTORICO):
        self.caminho_arquivo = caminho_arquivo
        self.registros: List[Dict] = []
        self._carregar()

    def _carregar(self):
        if os.path.exists(self.caminho_arquivo):
            try:
                with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                    self.registros = json.load(f)
            except (json.JSONDecodeError, TypeError):
                self.registros = []

    def salvar(self):
        with open(self.caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(self.registros, f, ensure_ascii=False, indent=2)

    def iniciar_execucao(self, pasta_saida: str, total_itens: int, perfis_usados: List[str]) -> str:
        exec_id = os.path.basename(pasta_saida)
        registro = {
            "id": exec_id,
            "pasta_saida": pasta_saida,
            "inicio": datetime.now().isoformat(timespec="seconds"),
            "fim": None,
            "total_itens": total_itens,
            "processados": 0,
            "sucessos": 0,
            "erros": 0,
            "perfis_usados": perfis_usados,
            "status": "Em andamento",
        }
        self.registros.insert(0, registro)
        self.salvar()
        return exec_id

    def atualizar_progresso(self, exec_id: str, processados: int, sucessos: int, erros: int):
        reg = self._obter(exec_id)
        if reg:
            reg["processados"] = processados
            reg["sucessos"] = sucessos
            reg["erros"] = erros
            self.salvar()

    def finalizar_execucao(self, exec_id: str, status: str = "Concluído"):
        reg = self._obter(exec_id)
        if reg:
            reg["fim"] = datetime.now().isoformat(timespec="seconds")
            reg["status"] = status
            self.salvar()

    def _obter(self, exec_id: str) -> Optional[Dict]:
        return next((r for r in self.registros if r["id"] == exec_id), None)

    def listar(self) -> List[Dict]:
        return self.registros
