# -*- coding: utf-8 -*-
"""paginas/logs.py — acompanhamento em tempo real, linha a linha, fiel ao
layout de referência (botão 'Limpar log' no canto superior direito)."""

import logging
import queue
import customtkinter as ctk
import estilo


class ManipuladorFilaLog(logging.Handler):
    """Handler de logging que empilha as mensagens numa fila thread-safe
    pra a UI consumir no laço principal do Tkinter."""

    def __init__(self, fila: queue.Queue):
        super().__init__()
        self.fila = fila

    def emit(self, record):
        self.fila.put(self.format(record))


class PaginaLogs(ctk.CTkFrame):
    NOME = "Logs"

    def __init__(self, master, app):
        super().__init__(master, fg_color=estilo.FUNDO)
        self.app = app
        self.fila_log = queue.Queue()
        self._montar()
        self._configurar_logging()
        self._consumir_fila()

    def _montar(self):
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 16))

        bloco_titulo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        bloco_titulo.pack(side="left")
        ctk.CTkLabel(
            bloco_titulo, text="Logs", font=(estilo.FONTE_PADRAO, estilo.FONTE_TITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            bloco_titulo, text="Acompanhe em tempo real o que a automação está fazendo.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w")

        ctk.CTkButton(
            cabecalho, text="🗑  Limpar log", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=self._limpar_log,
        ).pack(side="right")

        self.caixa_texto = ctk.CTkTextbox(
            self, fg_color=estilo.FUNDO_CARTAO, text_color=estilo.TEXTO_PRIMARIO, corner_radius=estilo.RAIO_CARTAO,
        )
        self.caixa_texto.pack(fill="both", expand=True)
        self.caixa_texto.configure(state="disabled")

    def _configurar_logging(self):
        handler = ManipuladorFilaLog(self.fila_log)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def _consumir_fila(self):
        while not self.fila_log.empty():
            linha = self.fila_log.get_nowait()
            self.caixa_texto.configure(state="normal")
            self.caixa_texto.insert("end", linha + "\n")
            self.caixa_texto.see("end")
            self.caixa_texto.configure(state="disabled")
        self.after(500, self._consumir_fila)

    def _limpar_log(self):
        self.caixa_texto.configure(state="normal")
        self.caixa_texto.delete("1.0", "end")
        self.caixa_texto.configure(state="disabled")

    def ao_exibir(self):
        pass
