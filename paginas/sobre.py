# -*- coding: utf-8 -*-
"""paginas/sobre.py — informações do programa, fiel ao layout de referência."""

import customtkinter as ctk
import estilo
import config


class PaginaSobre(ctk.CTkFrame):
    NOME = "Sobre"

    def __init__(self, master, app):
        super().__init__(master, fg_color=estilo.FUNDO)
        self.app = app
        self._montar()

    def _montar(self):
        ctk.CTkLabel(
            self, text="Sobre", font=(estilo.FONTE_PADRAO, estilo.FONTE_TITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            self, text="Informações do programa.", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO),
            text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(2, 20))

        painel = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel.pack(fill="x")

        ctk.CTkLabel(
            painel, text=config.NOME_APP, font=(estilo.FONTE_PADRAO, 18, "bold"), text_color=estilo.AZUL_MARINHO,
        ).pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(
            painel, text=f"Versão {config.VERSAO_APP}", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO),
            text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=20)

        ctk.CTkLabel(
            painel,
            text=("Automação para consulta e captura de dados de mensalidade de pós-graduação a partir de "
                  "uma lista de CPF's, com geração automática de link de pagamento das parcelas em aberto. "
                  "Suporta múltiplos perfis do Chrome em paralelo."),
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_PRIMARIO,
            wraplength=900, justify="left",
        ).pack(anchor="w", padx=20, pady=(10, 20))

    def ao_exibir(self):
        pass
