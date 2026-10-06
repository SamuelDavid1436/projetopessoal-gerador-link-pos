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
