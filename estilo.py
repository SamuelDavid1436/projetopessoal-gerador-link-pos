# -*- coding: utf-8 -*-
"""
estilo.py
Paleta de cores e tema da interface.
Tema CLARO, com azul marinho como cor de destaque (no lugar do verde) e
âmbar/dourado para ações principais. Mesma estrutura de variáveis do
projeto de referência — só os valores de cor mudam.
"""

# Fundos
FUNDO = "#F5F7FA"              # fundo geral (cinza bem claro)
FUNDO_CARTAO = "#FFFFFF"       # cartões / painéis
FUNDO_SECUNDARIO = "#EEF1F6"   # áreas secundárias, hover leve

# Cor de destaque principal (era verde -> agora azul marinho)
AZUL_MARINHO = "#12294B"
AZUL_MARINHO_HOVER = "#0B1C36"
AZUL_MARINHO_CLARO = "#274372"

# Cor de ação principal (era dourado -> âmbar combinando com azul marinho)
DOURADO = "#C79A3E"
DOURADO_HOVER = "#AD8330"
DOURADO_CLARO = "#E0B86C"

# Textos
TEXTO_PRIMARIO = "#1B2430"
TEXTO_SECUNDARIO = "#5B6675"
TEXTO_SOBRE_ESCURO = "#FFFFFF"

# Bordas / divisores
BORDA = "#DDE3EC"

# Estados
VERDE_SUCESSO = "#1E8E5A"
AMARELO_ALERTA = "#C79A3E"
VERMELHO_ERRO = "#C0392B"
AZUL_INFO = "#2E6FBB"

# Tipografia
FONTE_PADRAO = "Segoe UI"
FONTE_TITULO_TAMANHO = 20
FONTE_SUBTITULO_TAMANHO = 15
FONTE_TEXTO_TAMANHO = 13
FONTE_PEQUENA_TAMANHO = 11

# Raio de borda padrão dos cartões/botões (customtkinter usa em px)
RAIO_CARTAO = 12
RAIO_BOTAO = 8

TEMA_CTK = "light"  # modo claro fixo por padrão (alternável em Configurações)


def aplicar_tema_customtkinter():
    """Aplica o tema claro ao customtkinter (chamar uma vez no início)."""
    import customtkinter as ctk

    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
