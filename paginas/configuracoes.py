# -*- coding: utf-8 -*-
"""paginas/configuracoes.py — Tema / Pastas e arquivos / Estatísticas do
painel. Layout fiel ao projeto de referência."""

import os
import sys
import subprocess
import customtkinter as ctk
import estilo
import config


class PaginaConfiguracoes(ctk.CTkFrame):
    NOME = "Configurações"

    def __init__(self, master, app):
        super().__init__(master, fg_color=estilo.FUNDO)
        self.app = app
        self._montar()

    def _montar(self):
        ctk.CTkLabel(
            self, text="Configurações", font=(estilo.FONTE_PADRAO, estilo.FONTE_TITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            self, text="Ajustes de aparência e atalhos para as pastas do programa.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(2, 20))

        # conteúdo com rolagem: as seções não ficam cortadas em telas menores
        self.conteudo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.conteudo.pack(fill="both", expand=True)

        # ---- Tema ----
        painel_tema = ctk.CTkFrame(self.conteudo, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_tema.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            painel_tema, text="◐  Tema", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", padx=20, pady=(16, 8))

        self.seletor_tema = ctk.CTkSegmentedButton(
            painel_tema, values=["Azul Marinho", "Azul Claro", "Cinza Claro"], command=self._mudar_tema,
            fg_color=estilo.FUNDO_SECUNDARIO, selected_color=estilo.AZUL_MARINHO,
            selected_hover_color=estilo.AZUL_MARINHO_HOVER, unselected_color=estilo.FUNDO_SECUNDARIO,
            text_color=estilo.TEXTO_PRIMARIO,
        )
        self.seletor_tema.set("Azul Marinho")
        self.seletor_tema.pack(anchor="w", padx=20, pady=(0, 20))

        # ---- Pastas e arquivos ----
        painel_pastas = ctk.CTkFrame(self.conteudo, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_pastas.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            painel_pastas, text="📁  Pastas e arquivos", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", padx=20, pady=(16, 8))

        linha_botoes = ctk.CTkFrame(painel_pastas, fg_color="transparent")
        linha_botoes.pack(anchor="w", padx=20, pady=(0, 20))
        ctk.CTkButton(
            linha_botoes, text="📂 Abrir pasta Saída", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=lambda: self._abrir_pasta(config.DIR_SAIDA),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            linha_botoes, text="📂 Abrir pasta Logs", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=lambda: self._abrir_pasta(config.DIR_LOGS),
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            linha_botoes, text="✎ Limpar imagens de log", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=self._limpar_screenshots,
        ).pack(side="left", padx=8)

        # ---- Estatísticas do painel ----
        painel_stats = ctk.CTkFrame(self.conteudo, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_stats.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            painel_stats, text="▤  Estatísticas do painel", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            painel_stats,
            text=(
                '"Dados Capturados" soma todo o histórico de sucessos já registrado em '
                f'Logs\\log_processamento.json (desde a primeira vez que o programa rodou nesta máquina). '
                'Já a tabela de Execuções só mostra o que rodou depois que esse histórico passou a existir — '
                'por isso os números podem não bater exatamente. Isso é esperado, não é erro de contagem.'
            ),
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
            wraplength=1000, justify="left",
        ).pack(anchor="w", padx=20)

        ctk.CTkLabel(
            painel_stats,
            text=(
                "Se quiser começar a contagem do zero, o botão abaixo apaga apenas os arquivos de log e "
                "histórico do painel — os resultados já capturados na pasta Saída não são afetados."
            ),
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
            wraplength=1000, justify="left",
        ).pack(anchor="w", padx=20, pady=(6, 12))

        ctk.CTkButton(
            painel_stats, text="↻  Zerar estatísticas do painel", fg_color=estilo.FUNDO_SECUNDARIO,
            hover_color=estilo.BORDA, text_color=estilo.TEXTO_PRIMARIO, command=self._zerar_estatisticas,
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # ---- Zerar painel (novo polo) ----
        painel_zerar = ctk.CTkFrame(self.conteudo, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_zerar.pack(fill="x")
        ctk.CTkLabel(
            painel_zerar, text="🧹  Zerar painel (começar outro polo)",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"), text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            painel_zerar,
            text=(
                "Deixa o programa como novo antes da próxima execução: apaga os números do painel, o histórico "
                "de execuções, TODAS as pastas de saída (resultado, base_disparo, resultado_detalhado, "
                "reprocessar_erros) e as imagens de erro. Perfis e logins salvos NÃO são apagados.\n"
                "Copie os arquivos do polo anterior antes de zerar."
            ),
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
            wraplength=1000, justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))
        botoes_zerar = ctk.CTkFrame(painel_zerar, fg_color="transparent")
        botoes_zerar.pack(anchor="w", padx=20, pady=(0, 20))
        ctk.CTkButton(
            botoes_zerar, text="📂 Abrir pasta Saída", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=lambda: self._abrir_pasta(config.DIR_SAIDA),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            botoes_zerar, text="↻  Zerar painel", fg_color=estilo.VERMELHO_ERRO, hover_color="#96281F",
            command=self._zerar_painel,
        ).pack(side="left")

    # ------------------------------------------------------------------
    def _mudar_tema(self, valor):
        # O tema claro + azul marinho é o padrão do app (estilo.py). As
        # opções aqui existem para fidelidade ao layout de referência;
        # ajuste os valores em estilo.py se quiser variações reais de cor.
        pass

    def _abrir_pasta(self, caminho):
        os.makedirs(caminho, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(caminho)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])

    def _limpar_screenshots(self):
        pasta = config.DIR_SCREENSHOTS
        if os.path.exists(pasta):
            for nome in os.listdir(pasta):
                try:
                    os.remove(os.path.join(pasta, nome))
                except OSError:
                    pass

    def _zerar_painel(self):
        import limpeza
        limpeza.zerar_painel_com_confirmacao(self.app)

    def _zerar_estatisticas(self):
        self.app.estatisticas.zerar()
        self.app.historico.registros = []
        self.app.historico.salvar()
        pagina_inicio = self.app.paginas.get("Início")
        if pagina_inicio:
            pagina_inicio.ao_exibir()

    def ao_exibir(self):
        pass
