# -*- coding: utf-8 -*-
"""paginas/suporte.py — dicas rápidas, contato e botão 'Abrir manual de
uso'. Layout fiel ao projeto de referência."""

import os
import subprocess
import sys
import customtkinter as ctk
import estilo
import config


class PaginaSuporte(ctk.CTkFrame):
    NOME = "Suporte"

    def __init__(self, master, app):
        super().__init__(master, fg_color=estilo.FUNDO)
        self.app = app
        self._montar()

    def _montar(self):
        ctk.CTkLabel(
            self, text="Suporte", font=(estilo.FONTE_PADRAO, estilo.FONTE_TITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            self, text="Dúvidas ou problemas com a automação? Comece por aqui.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(2, 20))

        painel_dicas = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_dicas.pack(fill="x", pady=(0, 16))

        dicas = [
            "Verifique primeiro a aba Logs — a maioria dos erros aparece ali com uma mensagem clara.",
            "Screenshots de erro ficam salvos em Logs\\screenshots, um por CPF que falhou.",
            "Se um perfil ficar pedindo login de novo, verifique se a sessão do sistema expirou.",
            "Para reportar um problema, envie o arquivo de log (Logs\\log_processamento.json) e uma "
            "descrição do que aconteceu para o contato abaixo.",
        ]
        for dica in dicas:
            ctk.CTkLabel(
                painel_dicas, text=f"•  {dica}", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO),
                text_color=estilo.TEXTO_PRIMARIO, wraplength=1000, justify="left",
            ).pack(anchor="w", padx=20, pady=6)
        ctk.CTkFrame(painel_dicas, fg_color="transparent", height=8).pack()

        painel_contato = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_contato.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            painel_contato, text="☎  TELEFONE", font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO, "bold"),
            text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(
            painel_contato, text=config.SUPORTE_TELEFONE, font=(estilo.FONTE_PADRAO, 18, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", padx=20)

        ctk.CTkLabel(
            painel_contato, text="✉  E-MAIL", font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO, "bold"),
            text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=20, pady=(12, 0))
        ctk.CTkLabel(
            painel_contato, text=config.SUPORTE_EMAIL, font=(estilo.FONTE_PADRAO, 18, "bold"),
            text_color=estilo.AZUL_MARINHO,
        ).pack(anchor="w", padx=20, pady=(0, 16))

        painel_manual = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_manual.pack(fill="x")

        ctk.CTkLabel(
            painel_manual, text="▤  Manual de uso", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            painel_manual, text="O manual completo, com o passo a passo de cada tela, já vem junto com o programa.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=20)

        ctk.CTkButton(
            painel_manual, text="📄  Abrir manual de uso", fg_color=estilo.AZUL_MARINHO,
            hover_color=estilo.AZUL_MARINHO_HOVER, command=self._abrir_manual,
        ).pack(anchor="w", padx=20, pady=16)

    def _abrir_manual(self):
        # No .exe (PyInstaller, arquivo único) os assets ficam embutidos e são
        # extraídos em sys._MEIPASS; rodando pelo código-fonte, em ./assets.
        candidatos = []
        if getattr(sys, "_MEIPASS", None):
            candidatos.append(os.path.join(sys._MEIPASS, "assets", "manual.pdf"))
        candidatos.append(os.path.join(config.DIR_ASSETS, "manual.pdf"))
        caminho = next((c for c in candidatos if os.path.exists(c)), None)
        if caminho is None:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Manual não encontrado", "O arquivo do manual não foi encontrado junto do programa.")
            return
        if sys.platform == "win32":
            os.startfile(caminho)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])

    def ao_exibir(self):
        pass
