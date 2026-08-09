# -*- coding: utf-8 -*-
"""
credenciais.py
Armazena e recupera usuário/senha de login por perfil, usando o cofre de
credenciais do sistema operacional (Windows Credential Manager via
`keyring` — no macOS usa o Keychain, no Linux o Secret Service). A senha
NUNCA é gravada em texto puro em disco: fica em um cofre criptografado
gerenciado pelo próprio sistema operacional, atrelado à conta do usuário
do Windows que estiver logado na máquina.

Cada perfil (1, 2, 3) tem sua própria entrada no cofre, identificada por
um "serviço" único (NOME_SERVICO_BASE + id do perfil).
"""

import logging
from typing import Optional, Tuple

import keyring
import keyring.errors

import config

logger = logging.getLogger("credenciais")

NOME_SERVICO_BASE = "CapturaMensalidadePosGraduacao"


def _nome_servico(perfil_id: int) -> str:
    return f"{NOME_SERVICO_BASE}:perfil_{perfil_id}"


def salvar_credenciais(perfil_id: int, usuario: str, senha: str) -> bool:
    """Salva usuário/senha no cofre do sistema operacional para o perfil
    informado. Retorna True se conseguiu salvar."""
    if not usuario or not senha:
        return False
    try:
        servico = _nome_servico(perfil_id)
        # keyring guarda um par (serviço, usuário) -> senha. Guardamos o
        # nome de usuário também como "username" do keyring pra podermos
        # recuperá-lo depois sem precisar de outro arquivo.
        keyring.set_password(servico, "usuario", usuario)
        keyring.set_password(servico, usuario, senha)
        return True
    except keyring.errors.KeyringError:
        logger.exception("Falha ao salvar credenciais no cofre do sistema (perfil %s).", perfil_id)
        return False


def obter_credenciais(perfil_id: int) -> Optional[Tuple[str, str]]:
    """Retorna (usuario, senha) salvos pro perfil, ou None se não houver
    nada salvo (ou se o cofre não estiver disponível nessa máquina)."""
    try:
        servico = _nome_servico(perfil_id)
        usuario = keyring.get_password(servico, "usuario")
        if not usuario:
            return None
        senha = keyring.get_password(servico, usuario)
        if not senha:
            return None
        return usuario, senha
    except keyring.errors.KeyringError:
        logger.exception("Falha ao ler credenciais do cofre do sistema (perfil %s).", perfil_id)
        return None


def tem_credenciais(perfil_id: int) -> bool:
    return obter_credenciais(perfil_id) is not None


def remover_credenciais(perfil_id: int) -> None:
    """Remove as credenciais salvas do perfil (chamado por 'Limpar perfil')."""
    try:
        servico = _nome_servico(perfil_id)
        usuario = keyring.get_password(servico, "usuario")
        if usuario:
            try:
                keyring.delete_password(servico, usuario)
            except keyring.errors.PasswordDeleteError:
                pass
        try:
            keyring.delete_password(servico, "usuario")
        except keyring.errors.PasswordDeleteError:
            pass
    except keyring.errors.KeyringError:
        logger.exception("Falha ao remover credenciais do cofre do sistema (perfil %s).", perfil_id)
