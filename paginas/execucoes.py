# -*- coding: utf-8 -*-
"""paginas/execucoes.py — 'Importe a base de CPF's, escolha os perfis e
inicie a captura.' Layout fiel ao projeto de referência."""

import os
import sys
import threading
import subprocess
import tkinter.filedialog as filedialog
import customtkinter as ctk

import estilo
import config
import data_io
import runner as runner_mod
import estatisticas as estatisticas_mod


class PaginaExecucoes(ctk.CTkFrame):
    NOME = "Execuções"

    def __init__(self, master, app):
        super().__init__(master, fg_color=estilo.FUNDO)
        self.app = app
        self.caminho_base_selecionada = None
        self.checkboxes_perfis = {}
        self._montar()

    def _montar(self):
        ctk.CTkLabel(
            self, text="Execuções", font=(estilo.FONTE_PADRAO, estilo.FONTE_TITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            self, text="Importe a base de CPF's, escolha os perfis e inicie a captura.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(2, 20))

        painel_topo = ctk.CTkFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        painel_topo.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            painel_topo, text="Nova execução", font=(estilo.FONTE_PADRAO, estilo.FONTE_SUBTITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", padx=20, pady=(20, 12))

        linha_arquivo = ctk.CTkFrame(painel_topo, fg_color="transparent")
        linha_arquivo.pack(fill="x", padx=20)
        ctk.CTkLabel(
            linha_arquivo, text="Base com CPF's:", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(side="left")
        self.rotulo_arquivo = ctk.CTkLabel(
            linha_arquivo, text="  nenhum arquivo selecionado", text_color=estilo.TEXTO_SECUNDARIO,
        )
        self.rotulo_arquivo.pack(side="left")
        ctk.CTkButton(
            linha_arquivo, text="Importar base...", fg_color=estilo.AZUL_MARINHO,
            hover_color=estilo.AZUL_MARINHO_HOVER, command=self._selecionar_base,
        ).pack(side="right")

        ctk.CTkLabel(
            painel_topo,
            text=("Não é preciso separar a planilha por perfil: a automação divide a base de CPF's "
                  "automaticamente entre os perfis marcados abaixo e busca cada CPF direto no sistema, "
                  "capturando os dados de matrícula disponíveis."),
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.AZUL_MARINHO_CLARO,
            wraplength=1000, justify="left",
        ).pack(anchor="w", padx=20, pady=(6, 16))

        linha_perfis = ctk.CTkFrame(painel_topo, fg_color="transparent")
        linha_perfis.pack(fill="x", padx=20, pady=(0, 4))
        ctk.CTkLabel(
            linha_perfis, text="Perfis:", font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(side="left", padx=(0, 12))
        for perfil in self.app.gerenciador_perfis.perfis:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                linha_perfis, text=perfil.apelido, variable=var, fg_color=estilo.AZUL_MARINHO,
                hover_color=estilo.AZUL_MARINHO_HOVER,
            )
            cb.pack(side="left", padx=8)
            self.checkboxes_perfis[perfil.id] = var
        ctk.CTkLabel(
            linha_perfis, text="Marque um ou mais — cada um vira uma janela\ntrabalhando em paralelo.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
            justify="right",
        ).pack(side="right")

        linha_acao = ctk.CTkFrame(painel_topo, fg_color="transparent")
        linha_acao.pack(fill="x", padx=20, pady=(12, 20))
        self.botao_importar = ctk.CTkButton(
            linha_acao, text="↓  Importar", fg_color=estilo.AZUL_MARINHO, hover_color=estilo.AZUL_MARINHO_HOVER,
            width=140, command=self._iniciar_execucao,
        )
        self.botao_importar.pack(side="left")
        self.botao_parar = ctk.CTkButton(
            linha_acao, text="■  Parar", fg_color=estilo.VERMELHO_ERRO, hover_color="#96281F",
            width=110, command=self._parar_execucao, state="disabled",
        )
        self.botao_parar.pack(side="left", padx=8)

        ctk.CTkLabel(
            self, text="Histórico de execuções", font=(estilo.FONTE_PADRAO, estilo.FONTE_SUBTITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w", pady=(0, 8))

        self.lista_historico = ctk.CTkScrollableFrame(self, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)
        self.lista_historico.pack(fill="both", expand=True)

        self._atualizar_historico()

    # ------------------------------------------------------------------
    def _selecionar_base(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar base de CPFs",
            filetypes=[("Planilhas", "*.csv *.xlsx *.xls"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            self.caminho_base_selecionada = caminho
            self.rotulo_arquivo.configure(text=f"  {os.path.basename(caminho)}")

    def _iniciar_execucao(self):
        if not self.caminho_base_selecionada:
            return
        perfis_selecionados = [
            self.app.gerenciador_perfis.obter(pid) for pid, var in self.checkboxes_perfis.items() if var.get()
        ]
        if not perfis_selecionados:
            return

        df = data_io.ler_base_entrada(self.caminho_base_selecionada)
        cpfs = df["CPF"].tolist()
        pasta_saida = data_io.criar_pasta_saida()
        exec_id = self.app.historico.iniciar_execucao(pasta_saida, len(cpfs), [p.apelido for p in perfis_selecionados])

        self.app.runner_ativo = runner_mod.Runner(
            perfis_selecionados=perfis_selecionados,
            itens=cpfs,
            gerenciador_perfis=self.app.gerenciador_perfis,
            pasta_saida=pasta_saida,
            exec_id=exec_id,
            callback_inicio_item=self._callback_inicio_item,
            callback_resultado_item=self._callback_resultado_item,
        )

        self.botao_importar.configure(state="disabled")
        self.botao_parar.configure(state="normal")
        pagina_inicio = self.app.paginas.get("Início")
        if pagina_inicio:
            pagina_inicio.botao_parar.configure(state="normal")

        def worker():
            resultados = self.app.runner_ativo.executar()
            linhas_largas, colunas_largas = data_io.pivotar_para_wide(resultados)
            data_io.gravar_resultados(pasta_saida, linhas_largas, nome_base="resultado", colunas=colunas_largas)
            data_io.gravar_resultados(pasta_saida, resultados, nome_base="resultado_detalhado")
            data_io.gerar_base_reprocessamento(pasta_saida, linhas_largas)
            self.app.estatisticas.registrar_capturados(len(resultados))
            status_final = "Interrompido" if self.app.runner_ativo.foi_interrompido else "Concluído"
            self.app.historico.finalizar_execucao(exec_id, status=status_final)
            self.app.runner_ativo = None
            self.after(0, self._finalizar_execucao_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _parar_execucao(self):
        if self.app.runner_ativo:
            self.app.runner_ativo.parar()
        self.botao_parar.configure(state="disabled")

    def _finalizar_execucao_ui(self):
        self.botao_importar.configure(state="normal")
        self.botao_parar.configure(state="disabled")
        self._atualizar_historico()
        pagina_inicio = self.app.paginas.get("Início")
        if pagina_inicio:
            pagina_inicio.resetar_execucao_ui()
            pagina_inicio.ao_exibir()

    def _callback_inicio_item(self, cpf, apelido_perfil):
        pass

    def _callback_resultado_item(self, resultado, apelido_perfil):
        r = self.app.runner_ativo
        if r is None:
            return
        total = r.total_itens
        self.app.historico.atualizar_progresso(r.exec_id, r.processados, r.sucessos, r.erros)
        pagina_inicio = self.app.paginas.get("Início")
        if pagina_inicio:
            self.after(0, lambda: pagina_inicio.atualizar_progresso(
                r.processados, r.sucessos, total - r.processados, r.erros, total, apelido_perfil
            ))

    # ------------------------------------------------------------------
    def _atualizar_historico(self):
        for widget in self.lista_historico.winfo_children():
            widget.destroy()

        cores_status = {
            "Concluído": estilo.VERDE_SUCESSO,
            "Interrompido": estilo.VERMELHO_ERRO,
            "Em andamento": estilo.AZUL_INFO,
        }

        for registro in self.app.historico.listar():
            linha = ctk.CTkFrame(self.lista_historico, fg_color=estilo.FUNDO_SECUNDARIO, corner_radius=8)
            linha.pack(fill="x", padx=8, pady=4)

            duracao = estatisticas_mod.formatar_duracao(estatisticas_mod.duracao_segundos(registro))
            data_fmt = registro["inicio"].replace("T", " ")

            texto = f"{data_fmt}   •   {len(registro['perfis_usados'])} perfil(is)"
            ctk.CTkLabel(linha, text=texto, text_color=estilo.TEXTO_PRIMARIO).pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(
                linha, text=registro["status"], text_color=cores_status.get(registro["status"], estilo.TEXTO_PRIMARIO),
                font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO, "bold"),
            ).pack(side="left", padx=12)

            ctk.CTkLabel(
                linha, text=f"{registro['processados']}/{registro['total_itens']} registros  •  {duracao}",
                text_color=estilo.TEXTO_SECUNDARIO,
            ).pack(side="left", padx=12)

            ctk.CTkButton(
                linha, text="Abrir pasta", width=110, fg_color=estilo.AZUL_MARINHO,
                hover_color=estilo.AZUL_MARINHO_HOVER,
                command=lambda p=registro["pasta_saida"]: self._abrir_pasta(p),
            ).pack(side="right", padx=6, pady=6)

            ctk.CTkButton(
                linha, text="Reprocessar erros", width=140, fg_color=estilo.DOURADO,
                hover_color=estilo.DOURADO_HOVER, text_color=estilo.TEXTO_PRIMARIO,
                command=lambda p=registro["pasta_saida"]: self._usar_reprocessamento(p),
            ).pack(side="right", padx=6, pady=6)

    def _abrir_pasta(self, caminho):
        if not os.path.exists(caminho):
            return
        if sys.platform == "win32":
            os.startfile(caminho)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])

    def _usar_reprocessamento(self, pasta_saida):
        caminho = os.path.join(pasta_saida, "reprocessar_erros.xlsx")
        if os.path.exists(caminho):
            self.caminho_base_selecionada = caminho
            self.rotulo_arquivo.configure(text=f"  {os.path.basename(caminho)}")

    def ao_exibir(self):
        self._atualizar_historico()
