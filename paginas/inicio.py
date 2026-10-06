# -*- coding: utf-8 -*-
"""paginas/inicio.py — 'Bem-vindo!', cartões de resumo, execução em
andamento e execuções recentes. Layout fiel ao projeto de referência."""

import customtkinter as ctk
import estilo
import estatisticas as estatisticas_mod


class PaginaInicio(ctk.CTkFrame):
    NOME = "Início"

    def __init__(self, master, app):
        super().__init__(master, fg_color=estilo.FUNDO)
        self.app = app
        self._montar()

    # ------------------------------------------------------------------
    def _montar(self):
        self.grid_columnconfigure(0, weight=1)

        # ---- Cabeçalho ----
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        cabecalho.grid_columnconfigure(0, weight=1)

        bloco_titulo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        bloco_titulo.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            bloco_titulo, text="Bem-vindo!", font=(estilo.FONTE_PADRAO, estilo.FONTE_TITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            bloco_titulo, text="Gerencie as execuções e acompanhe o progresso da captura de dados.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(2, 0))

        bloco_botoes = ctk.CTkFrame(cabecalho, fg_color="transparent")
        bloco_botoes.grid(row=0, column=1, sticky="e")
        self.botao_parar = ctk.CTkButton(
            bloco_botoes, text="■  Parar", fg_color=estilo.VERMELHO_ERRO, hover_color="#96281F",
            width=100, command=self._parar_execucao, state="disabled",
        )
        self.botao_parar.pack(side="left", padx=(0, 8))
        self.botao_zerar = ctk.CTkButton(
            bloco_botoes, text="↻  Zerar painel", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, width=130, command=self._zerar_painel,
        )
        self.botao_zerar.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            bloco_botoes, text="+  Nova Execução", fg_color=estilo.DOURADO, hover_color=estilo.DOURADO_HOVER,
            text_color=estilo.TEXTO_PRIMARIO, width=150,
            command=lambda: self.app.mostrar_pagina("Execuções"),
        ).pack(side="left")

        # ---- Cartões de resumo ----
        cartoes_frame = ctk.CTkFrame(self, fg_color="transparent")
        cartoes_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        for i in range(4):
            cartoes_frame.grid_columnconfigure(i, weight=1)

        self.cartoes = {}
        definicoes = [
            ("Dados Capturados (histórico total)", "📄"),
            ("Perfis Selecionados", "👤"),
            ("Execuções Hoje", "⟳"),
            ("Tempo Total Hoje", "⏱"),
        ]
        for i, (rotulo, icone) in enumerate(definicoes):
            cartao, rotulo_valor = self._criar_cartao_resumo(cartoes_frame, rotulo, icone)
            cartao.grid(row=0, column=i, sticky="nsew", padx=6)
            self.cartoes[rotulo] = rotulo_valor

        # ---- Execução em andamento ----
        self.painel_execucao = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        self.painel_execucao.grid(row=2, column=0, sticky="ew", pady=(0, 16))

        faixa_lateral = ctk.CTkFrame(self.painel_execucao, fg_color=estilo.AZUL_MARINHO, width=5, corner_radius=0)
        faixa_lateral.pack(side="left", fill="y")

        conteudo_execucao = ctk.CTkFrame(self.painel_execucao, fg_color="transparent")
        conteudo_execucao.pack(side="left", fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            conteudo_execucao, text="Execução em andamento",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_SUBTITULO_TAMANHO, "bold"), text_color=estilo.AZUL_MARINHO,
        ).pack(anchor="w")

        self.rotulo_status_execucao = ctk.CTkLabel(
            conteudo_execucao, text='Nenhuma execução em andamento no momento. Clique em "Nova Execução" para começar.',
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        )
        self.rotulo_status_execucao.pack(anchor="w", pady=(6, 0))

        self.barra_progresso = ctk.CTkProgressBar(conteudo_execucao, progress_color=estilo.AZUL_MARINHO)
        self.barra_progresso.set(0)

        self.frame_blocos_execucao = ctk.CTkFrame(conteudo_execucao, fg_color="transparent")
        self.blocos_execucao = {}

        # ---- Execuções recentes ----
        ctk.CTkLabel(
            self, text="Execuções recentes", font=(estilo.FONTE_PADRAO, estilo.FONTE_SUBTITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).grid(row=3, column=0, sticky="w", pady=(0, 8))

        self.frame_tabela = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        self.frame_tabela.grid(row=4, column=0, sticky="ew")

        ctk.CTkButton(
            self, text="Ver todas as execuções", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=lambda: self.app.mostrar_pagina("Execuções"),
        ).grid(row=5, column=0, pady=12)

        self._preencher_tabela_recentes()

    # ------------------------------------------------------------------
    def _criar_cartao_resumo(self, master, rotulo, icone):
        cartao = ctk.CTkFrame(master, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)

        cabecalho = ctk.CTkFrame(cartao, fg_color="transparent")
        cabecalho.pack(fill="x", padx=16, pady=(16, 0))

        selo_icone = ctk.CTkLabel(
            cabecalho, text=icone, width=36, height=36, corner_radius=8, fg_color=estilo.FUNDO_SECUNDARIO,
            font=(estilo.FONTE_PADRAO, 16),
        )
        selo_icone.pack(anchor="w")

        rotulo_valor = ctk.CTkLabel(
            cartao, text="0", font=(estilo.FONTE_PADRAO, 26, "bold"), text_color=estilo.AZUL_MARINHO,
        )
        rotulo_valor.pack(anchor="w", padx=16, pady=(8, 0))

        ctk.CTkLabel(
            cartao, text=rotulo, font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO),
            text_color=estilo.TEXTO_SECUNDARIO, wraplength=200, justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 16))

        return cartao, rotulo_valor

    # ------------------------------------------------------------------
    def atualizar_progresso(self, processados, sucessos, pendentes, erros, total, perfil_atual=""):
        pct = (processados / total) if total else 0
        self.barra_progresso.set(pct)
        if not self.barra_progresso.winfo_ismapped():
            self.barra_progresso.pack(fill="x", pady=(12, 12))
            self.frame_blocos_execucao.pack(fill="x")

        self.rotulo_status_execucao.configure(
            text=f"Perfil ativo: {perfil_atual}  •  {processados}/{total} processados ({pct*100:.0f}%)"
        )

        blocos = [("Processados", processados), ("Sucessos", sucessos), ("Pendentes", pendentes), ("Erros", erros)]
        if not self.blocos_execucao:
            for i, (nome, _valor) in enumerate(blocos):
                bloco = ctk.CTkFrame(self.frame_blocos_execucao, fg_color=estilo.FUNDO_SECUNDARIO, corner_radius=8)
                bloco.grid(row=0, column=i, sticky="nsew", padx=(0, 8) if i < 3 else (0, 0))
                self.frame_blocos_execucao.grid_columnconfigure(i, weight=1)
                valor_lbl = ctk.CTkLabel(bloco, text="0", font=(estilo.FONTE_PADRAO, 20, "bold"), text_color=estilo.AZUL_MARINHO)
                valor_lbl.pack(pady=(10, 0))
                ctk.CTkLabel(bloco, text=nome, font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO).pack(pady=(0, 10))
                self.blocos_execucao[nome] = valor_lbl

        for nome, valor in blocos:
            self.blocos_execucao[nome].configure(text=str(valor))

    def resetar_execucao_ui(self):
        self.barra_progresso.pack_forget()
        self.frame_blocos_execucao.pack_forget()
        self.rotulo_status_execucao.configure(
            text='Nenhuma execução em andamento no momento. Clique em "Nova Execução" para começar.'
        )
        self.botao_parar.configure(state="disabled")

    # ------------------------------------------------------------------
    def _preencher_tabela_recentes(self):
        for widget in self.frame_tabela.winfo_children():
            widget.destroy()

        cabecalhos = ["Data/Hora", "Perfis", "Status", "Registros", "Duração", ""]
        larguras = [3, 2, 2, 2, 2, 1]
        linha_cab = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        linha_cab.pack(fill="x", padx=16, pady=(12, 4))
        for i, texto in enumerate(cabecalhos):
            ctk.CTkLabel(
                linha_cab, text=texto, font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO, "bold"),
                text_color=estilo.TEXTO_SECUNDARIO, width=larguras[i] * 60, anchor="w",
            ).pack(side="left")

        registros = self.app.historico.listar()[:4]
        if not registros:
            ctk.CTkLabel(
                self.frame_tabela, text="Nenhuma execução registrada ainda.",
                text_color=estilo.TEXTO_SECUNDARIO,
            ).pack(padx=16, pady=(4, 16), anchor="w")
            return

        cores_status = {
            "Concluído": estilo.VERDE_SUCESSO,
            "Interrompido": estilo.VERMELHO_ERRO,
            "Em andamento": estilo.AZUL_INFO,
        }

        for registro in registros:
            linha = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
            linha.pack(fill="x", padx=16, pady=4)

            data_fmt = registro["inicio"].replace("T", " ")
            duracao = estatisticas_mod.formatar_duracao(estatisticas_mod.duracao_segundos(registro))

            ctk.CTkLabel(linha, text=data_fmt, text_color=estilo.TEXTO_PRIMARIO, width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(linha, text=f"{len(registro['perfis_usados'])} perfil(is)", text_color=estilo.TEXTO_PRIMARIO, width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(
                linha, text=registro["status"], text_color=cores_status.get(registro["status"], estilo.TEXTO_PRIMARIO),
                width=120, anchor="w", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            ).pack(side="left")
            ctk.CTkLabel(linha, text=str(registro["processados"]), text_color=estilo.TEXTO_PRIMARIO, width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(linha, text=duracao, text_color=estilo.TEXTO_PRIMARIO, width=120, anchor="w").pack(side="left")

            import os
            def abrir(p=registro["pasta_saida"]):
                self._abrir_pasta(p)
            ctk.CTkButton(
                linha, text="📁", width=32, fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
                text_color=estilo.TEXTO_PRIMARIO, command=abrir,
            ).pack(side="left")

        ctk.CTkFrame(self.frame_tabela, fg_color="transparent", height=8).pack()

    def _abrir_pasta(self, caminho):
        import os, sys, subprocess
        if not os.path.exists(caminho):
            return
        if sys.platform == "win32":
            os.startfile(caminho)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])

    def _zerar_painel(self):
        import limpeza
        limpeza.zerar_painel_com_confirmacao(self.app)

    def _parar_execucao(self):
        if self.app.runner_ativo:
            self.app.runner_ativo.parar()
        self.botao_parar.configure(state="disabled")

    # ------------------------------------------------------------------
    def ao_exibir(self):
        self.cartoes["Dados Capturados (histórico total)"].configure(
            text=str(self.app.estatisticas.total_capturados())
        )
        perfis_logados = sum(1 for p in self.app.gerenciador_perfis.perfis if p.status == "Logado")
        self.cartoes["Perfis Selecionados"].configure(text=str(perfis_logados))

        registros = self.app.historico.listar()
        self.cartoes["Execuções Hoje"].configure(text=str(estatisticas_mod.execucoes_hoje(registros)))
        self.cartoes["Tempo Total Hoje"].configure(
            text=estatisticas_mod.formatar_duracao(estatisticas_mod.tempo_total_hoje_segundos(registros))
        )
        self._preencher_tabela_recentes()
        self.botao_parar.configure(state="normal" if self.app.runner_ativo else "disabled")
