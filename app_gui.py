# -*- coding: utf-8 -*-
"""
app_gui.py
Controlador principal da interface (customtkinter) + navegação entre
páginas. Layout fiel ao projeto de referência: barra lateral com
ícone/nome do app, faixa superior com indicadores de desempenho
(FPS/GPU/CPU/LAT), e área de conteúdo por página.
"""

import logging
import os

import customtkinter as ctk

try:
    import psutil
except ImportError:  # psutil é opcional — a faixa de status cai pra "N/A"
    psutil = None

import config
import estilo
import perfis as perfis_mod
import history as history_mod
import recuperacao as recuperacao_mod
import estatisticas as estatisticas_mod

from paginas import inicio, perfis as pagina_perfis, execucoes, configuracoes, logs as pagina_logs, suporte, sobre

logger = logging.getLogger("app_gui")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        estilo.aplicar_tema_customtkinter()

        self.title(config.NOME_APP)
        self.geometry("1250x760")
        self.minsize(1050, 650)
        self.configure(fg_color=estilo.FUNDO)

        icone = os.path.join(config.DIR_ASSETS, "icone.ico")
        if os.path.exists(icone):
            try:
                self.iconbitmap(icone)
            except Exception:
                pass

        # Estado compartilhado
        self.gerenciador_perfis = perfis_mod.GerenciadorPerfis()
        self.historico = history_mod.Historico()
        self.log_recuperacao = recuperacao_mod.LogRecuperacao()
        self.estatisticas = estatisticas_mod.Estatisticas()
        self.runner_ativo = None

        self._montar_layout()
        self._atualizar_faixa_status()
        self._checar_recuperacao_pendente()

    # ------------------------------------------------------------------
    def _montar_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._montar_faixa_status()
        self._montar_menu_lateral()

        self.container_paginas = ctk.CTkFrame(self, fg_color=estilo.FUNDO)
        self.container_paginas.grid(row=1, column=1, sticky="nsew", padx=24, pady=16)
        self.container_paginas.grid_rowconfigure(0, weight=1)
        self.container_paginas.grid_columnconfigure(0, weight=1)

        self.paginas = {}
        for Classe in (
            inicio.PaginaInicio,
            pagina_perfis.PaginaPerfis,
            execucoes.PaginaExecucoes,
            configuracoes.PaginaConfiguracoes,
            pagina_logs.PaginaLogs,
            suporte.PaginaSuporte,
            sobre.PaginaSobre,
        ):
            pagina = Classe(self.container_paginas, self)
            self.paginas[Classe.NOME] = pagina
            pagina.grid(row=0, column=0, sticky="nsew")

        self.mostrar_pagina("Início")

    # ------------------------------------------------------------------
    def _montar_faixa_status(self):
        """Faixa superior fina com indicadores de desempenho, como no
        projeto de referência (FPS / GPU / CPU / LAT)."""
        faixa = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, height=30, corner_radius=0)
        faixa.grid(row=0, column=0, columnspan=2, sticky="ew")
        faixa.grid_propagate(False)

        self.rotulo_status_desempenho = ctk.CTkLabel(
            faixa, text="FPS N/A  |  GPU N/A  |  CPU N/A  |  LAT N/A",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO),
            text_color=estilo.TEXTO_SECUNDARIO,
        )
        self.rotulo_status_desempenho.pack(side="right", padx=16, pady=4)

    def _atualizar_faixa_status(self):
        cpu_texto = "N/A"
        if psutil is not None:
            try:
                cpu_texto = f"{psutil.cpu_percent(interval=None):.0f}%"
            except Exception:
                cpu_texto = "N/A"
        self.rotulo_status_desempenho.configure(
            text=f"FPS N/A  |  GPU N/A  |  CPU {cpu_texto}  |  LAT N/A"
        )
        self.after(2000, self._atualizar_faixa_status)

    # ------------------------------------------------------------------
    def _montar_menu_lateral(self):
        menu = ctk.CTkFrame(self, fg_color=estilo.AZUL_MARINHO, width=230, corner_radius=0)
        menu.grid(row=1, column=0, sticky="nsw")
        menu.grid_propagate(False)

        cabecalho = ctk.CTkFrame(menu, fg_color="transparent")
        cabecalho.pack(fill="x", padx=20, pady=(24, 20), anchor="w")

        icone_png = os.path.join(config.DIR_ASSETS, "icone.png")
        if os.path.exists(icone_png):
            try:
                from PIL import Image
                img = ctk.CTkImage(Image.open(icone_png), size=(40, 40))
                ctk.CTkLabel(cabecalho, image=img, text="").pack(anchor="w", pady=(0, 10))
            except Exception:
                pass

        ctk.CTkLabel(
            cabecalho, text=config.NOME_APP_LINHA1, font=(estilo.FONTE_PADRAO, 19, "bold"),
            text_color="#FFFFFF", justify="left",
        ).pack(anchor="w")
        ctk.CTkLabel(
            cabecalho, text=config.NOME_APP_LINHA2, font=(estilo.FONTE_PADRAO, 19, "bold"),
            text_color=estilo.DOURADO_CLARO, justify="left",
        ).pack(anchor="w")
        ctk.CTkLabel(
            cabecalho, text=config.NOME_APP_SUBTITULO, font=(estilo.FONTE_PADRAO, 11),
            text_color="#B7C2D6", justify="left",
        ).pack(anchor="w", pady=(8, 0))

        itens = ["Início", "Perfis", "Execuções", "Configurações", "Logs", "Suporte", "Sobre"]
        self.botoes_menu = {}
        for nome in itens:
            btn = ctk.CTkButton(
                menu, text=nome, anchor="w", fg_color="transparent",
                hover_color=estilo.AZUL_MARINHO_HOVER, text_color="#FFFFFF",
                font=(estilo.FONTE_PADRAO, 14), corner_radius=8,
                command=lambda n=nome: self.mostrar_pagina(n),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.botoes_menu[nome] = btn

    # ------------------------------------------------------------------
    def mostrar_pagina(self, nome: str):
        pagina = self.paginas.get(nome)
        if pagina is None:
            return
        pagina.tkraise()
        if hasattr(pagina, "ao_exibir"):
            pagina.ao_exibir()
        for n, btn in self.botoes_menu.items():
            btn.configure(fg_color=estilo.DOURADO if n == nome else "transparent",
                           text_color=estilo.TEXTO_PRIMARIO if n == nome else "#FFFFFF")

    # ------------------------------------------------------------------
    def _checar_recuperacao_pendente(self):
        if self.log_recuperacao.existe_pendente():
            estado = self.log_recuperacao.carregar()
            if estado:
                self._perguntar_recuperacao(estado)

    def _perguntar_recuperacao(self, estado):
        janela = ctk.CTkToplevel(self)
        janela.title("Recuperar execução")
        janela.geometry("460x200")
        janela.configure(fg_color=estilo.FUNDO_CARTAO)

        qtd = len(estado.get("resultados_parciais", []))
        total = estado.get("itens_totais", 0)
        ctk.CTkLabel(
            janela,
            text=(
                f"Uma execução anterior foi interrompida.\n"
                f"{qtd} de {total} itens já haviam sido processados.\n\n"
                "Deseja recuperar os resultados parciais?"
            ),
            font=(estilo.FONTE_PADRAO, 13), text_color=estilo.TEXTO_PRIMARIO, justify="left",
        ).pack(padx=20, pady=20)

        frame_botoes = ctk.CTkFrame(janela, fg_color="transparent")
        frame_botoes.pack(pady=10)

        def recuperar():
            import data_io
            linhas = []
            for r in estado.get("resultados_parciais", []):
                linhas.extend(r.get("linhas", []))
            linhas_largas, colunas_largas = data_io.pivotar_para_wide(linhas)
            data_io.gravar_resultados(
                estado["pasta_saida"], linhas_largas, nome_base="resultado_recuperado", colunas=colunas_largas
            )
            data_io.gravar_resultados(estado["pasta_saida"], linhas, nome_base="resultado_recuperado_detalhado")
            self.estatisticas.registrar_capturados(len(linhas))
            self.log_recuperacao.limpar()
            janela.destroy()

        def descartar():
            self.log_recuperacao.limpar()
            janela.destroy()

        ctk.CTkButton(
            frame_botoes, text="Recuperar", fg_color=estilo.DOURADO, hover_color=estilo.DOURADO_HOVER,
            text_color=estilo.TEXTO_PRIMARIO, command=recuperar,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            frame_botoes, text="Descartar", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=descartar,
        ).pack(side="left", padx=8)
