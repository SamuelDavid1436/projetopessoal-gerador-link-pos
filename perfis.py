# -*- coding: utf-8 -*-
"""
perfis.py
Metadados persistidos de cada perfil (apelido, e-mail, status, pasta de
dados do Chrome). Suporta até 3 perfis independentes.
"""

import json
import os
import shutil
from dataclasses import dataclass, asdict, field
from typing import List, Optional

import config

MAX_PERFIS = 3


@dataclass
class Perfil:
    id: int
    apelido: str = ""
    apelido_personalizado: bool = False
    email: str = ""
    email_personalizado: bool = False
    status: str = "Não logado"  # "Não logado" | "Logado" | "Verificando..."
    pasta_dados: str = ""

    def __post_init__(self):
        if not self.pasta_dados:
            self.pasta_dados = os.path.join(config.DIR_PERFIS_CHROME, f"perfil_{self.id}")
        if not self.apelido:
            self.apelido = f"Perfil {self.id}"


class GerenciadorPerfis:
    """Carrega, salva e migra os metadados de perfis."""

    def __init__(self, caminho_arquivo: str = config.ARQ_PERFIS):
        self.caminho_arquivo = caminho_arquivo
        self.perfis: List[Perfil] = []
        self._carregar()
        self._migrar_dados_antigos()

    # ------------------------------------------------------------------
    def _carregar(self):
        if os.path.exists(self.caminho_arquivo):
            try:
                with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.perfis = [Perfil(**p) for p in dados]
            except (json.JSONDecodeError, TypeError):
                self.perfis = []
        if not self.perfis:
            self.perfis = [Perfil(id=i) for i in range(1, MAX_PERFIS + 1)]
            self.salvar()

    def salvar(self):
        with open(self.caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in self.perfis], f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    def _migrar_dados_antigos(self):
        """Se houver pasta de perfil antiga em local errado (ex.: Documentos/
        OneDrive), migra automaticamente para %LOCALAPPDATA%."""
        locais_antigos = [
            os.path.join(os.path.expanduser("~"), "Documents", "CapturaLinkKroton", "PerfisChrome"),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Documentos", "CapturaLinkKroton", "PerfisChrome"),
        ]
        for perfil in self.perfis:
            if os.path.exists(perfil.pasta_dados):
                continue
            for local_antigo in locais_antigos:
                origem = os.path.join(local_antigo, f"perfil_{perfil.id}")
                if os.path.exists(origem):
                    try:
                        shutil.move(origem, perfil.pasta_dados)
                    except OSError:
                        pass
                    break

    # ------------------------------------------------------------------
    def obter(self, perfil_id: int) -> Optional[Perfil]:
        return next((p for p in self.perfis if p.id == perfil_id), None)

    def atualizar_apelido(self, perfil_id: int, novo_apelido: str, personalizado: bool = True):
        p = self.obter(perfil_id)
        if p:
            p.apelido = novo_apelido
            p.apelido_personalizado = personalizado
            self.salvar()

    def atualizar_email_detectado(self, perfil_id: int, email: str):
        """Chamado pelo monitor de login. Só sobrescreve apelido se ele
        ainda não tiver sido personalizado pelo usuário."""
        p = self.obter(perfil_id)
        if not p:
            return
        p.email = email
        if not p.email_personalizado:
            pass  # e-mail em si não é "personalizável" por padrão, sempre reflete detecção
        if not p.apelido_personalizado:
            p.apelido = email
        self.salvar()

    def atualizar_email_manual(self, perfil_id: int, email: str):
        p = self.obter(perfil_id)
        if p:
            p.email = email
            p.email_personalizado = True
            self.salvar()

    def atualizar_status(self, perfil_id: int, status: str):
        p = self.obter(perfil_id)
        if p:
            p.status = status
            self.salvar()

    def limpar_perfil(self, perfil_id: int):
        """Reseta login + apelido + e-mail + credenciais salvas daquele perfil."""
        p = self.obter(perfil_id)
        if not p:
            return
        if os.path.exists(p.pasta_dados):
            shutil.rmtree(p.pasta_dados, ignore_errors=True)
        try:
            import credenciais as credenciais_mod
            credenciais_mod.remover_credenciais(perfil_id)
        except ImportError:
            pass
        p.apelido = f"Perfil {p.id}"
        p.apelido_personalizado = False
        p.email = ""
        p.email_personalizado = False
        p.status = "Não logado"
        self.salvar()
