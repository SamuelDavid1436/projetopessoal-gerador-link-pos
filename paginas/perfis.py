# -*- coding: utf-8 -*-
"""paginas/perfis.py — cartões por perfil, fiéis ao layout de referência:
título + lápis editável, badge de status (Logado / sem login salvo),
e-mail + lápis, pasta local, e os três botões de ação."""

import os
import threading
import customtkinter as ctk
import estilo
import browser_manager
import credenciais as credenciais_mod


class PaginaPerfis(ctk.CTkFrame):
    NOME = "Perfis"

    def __init__(self, master, app):
        super().__init__(master, fg_color=estilo.FUNDO)
        self.app = app
        self.cartoes_widgets = {}
        self._montar()

    def _montar(self):
        ctk.CTkLabel(
            self, text="Perfis", font=(estilo.FONTE_PADRAO, estilo.FONTE_TITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            self,
            text=("Cada perfil guarda um login independente do Chrome. Na primeira vez, digite usuário "
                  "e senha manualmente — o apelido do perfil é preenchido automaticamente com o usuário "
                  "digitado, e as credenciais ficam salvas com segurança no cofre do Windows. Da próxima "
                  "vez, é só clicar em 'Entrar (login automático)' que ele loga sozinho. Use os lápis (✎) "
                  "pra personalizar o apelido ou corrigir o e-mail manualmente."),
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
            wraplength=900, justify="left",
        ).pack(anchor="w", pady=(2, 20))

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        for i, perfil in enumerate(self.app.gerenciador_perfis.perfis):
            container.grid_columnconfigure(i, weight=1)
            self._criar_cartao_perfil(container, perfil).grid(row=0, column=i, padx=8, sticky="new")

    def _criar_cartao_perfil(self, container, perfil):
        cartao = ctk.CTkFrame(container, fg_color=estilo.FUNDO_CARTAO, corner_radius=estilo.RAIO_CARTAO)

        linha_titulo = ctk.CTkFrame(cartao, fg_color="transparent")
        linha_titulo.pack(fill="x", padx=16, pady=(16, 4))

        bloco_nome = ctk.CTkFrame(linha_titulo, fg_color="transparent")
        bloco_nome.pack(side="left")
        rotulo_apelido = ctk.CTkLabel(
            bloco_nome, text=perfil.apelido, font=(estilo.FONTE_PADRAO, estilo.FONTE_SUBTITULO_TAMANHO, "bold"),
            text_color=estilo.TEXTO_PRIMARIO,
        )
        rotulo_apelido.pack(side="left")

        badge_status = ctk.CTkLabel(
            linha_titulo, text=self._texto_badge(perfil.status), corner_radius=10,
            fg_color=self._cor_badge(perfil.status), text_color="#FFFFFF",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO, "bold"), padx=10, pady=2,
        )
        badge_status.pack(side="right")

        def editar_apelido():
            entrada = ctk.CTkInputDialog(text="Novo apelido para o perfil:", title="Editar apelido")
            novo = entrada.get_input()
            if novo:
                self.app.gerenciador_perfis.atualizar_apelido(perfil.id, novo)
                self._atualizar_cartao(perfil.id)

        ctk.CTkButton(
            linha_titulo, text="✎", width=24, height=24, fg_color="transparent",
            hover_color=estilo.FUNDO_SECUNDARIO, text_color=estilo.TEXTO_SECUNDARIO, command=editar_apelido,
        ).pack(side="left", padx=(4, 0))

        linha_email = ctk.CTkFrame(cartao, fg_color="transparent")
        linha_email.pack(fill="x", padx=16, pady=(4, 2))
        rotulo_email = ctk.CTkLabel(
            linha_email, text=f"E-mail: {perfil.email or 'ainda não detectado'}",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        )
        rotulo_email.pack(side="left")

        def editar_email():
            entrada = ctk.CTkInputDialog(text="E-mail deste perfil:", title="Editar e-mail")
            novo = entrada.get_input()
            if novo:
                self.app.gerenciador_perfis.atualizar_email_manual(perfil.id, novo)
                self._atualizar_cartao(perfil.id)

        ctk.CTkButton(
            linha_email, text="✎", width=22, height=22, fg_color="transparent",
            hover_color=estilo.FUNDO_SECUNDARIO, text_color=estilo.TEXTO_SECUNDARIO, command=editar_email,
        ).pack(side="left", padx=(4, 0))

        rotulo_pasta = ctk.CTkLabel(
            cartao, text=f"Pasta local: {os.path.basename(perfil.pasta_dados)}",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
        )
        rotulo_pasta.pack(anchor="w", padx=16, pady=(0, 4))

        rotulo_credenciais = ctk.CTkLabel(
            cartao, text=self._texto_credenciais(perfil.id),
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO),
            text_color=self._cor_credenciais(perfil.id),
        )
        rotulo_credenciais.pack(anchor="w", padx=16, pady=(0, 12))

        frame_botoes = ctk.CTkFrame(cartao, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=16, pady=(0, 16))

        botao_login = None

        def login_manual():
            if browser_manager.perfil_tem_navegador_aberto(perfil.id):
                self._mostrar_aviso(
                    "Janela já aberta",
                    f"Já existe uma janela de login aberta para o perfil '{perfil.apelido}'.\n\n"
                    "Finalize o login nela (ou feche-a) antes de abrir outra — duas janelas do "
                    "Chrome usando o mesmo perfil ao mesmo tempo é exatamente o que faz o login "
                    "não ser salvo de verdade.",
                )
                return
            try:
                browser_manager.login_manual(perfil, self.app.gerenciador_perfis)
            except browser_manager.PerfilEmUsoError as e:
                self._mostrar_aviso("Janela já aberta", str(e))
                return
            self.after(2000, lambda: self._atualizar_cartao(perfil.id))

        def verificar_login():
            if browser_manager.perfil_tem_navegador_aberto(perfil.id):
                self._mostrar_aviso(
                    "Janela já aberta",
                    f"Há uma janela de login aberta para o perfil '{perfil.apelido}'. "
                    "Feche-a antes de verificar o login.",
                )
                return

            def worker():
                try:
                    browser_manager.verificar_login(perfil, self.app.gerenciador_perfis)
                except browser_manager.PerfilEmUsoError:
                    pass
                self.after(0, lambda: self._atualizar_cartao(perfil.id))
            threading.Thread(target=worker, daemon=True).start()

        def limpar_perfil():
            if browser_manager.perfil_tem_navegador_aberto(perfil.id):
                self._mostrar_aviso(
                    "Janela já aberta",
                    f"Feche a janela de login aberta do perfil '{perfil.apelido}' antes de limpá-lo.",
                )
                return
            self.app.gerenciador_perfis.limpar_perfil(perfil.id)
            self._atualizar_cartao(perfil.id)

        ctk.CTkButton(
            frame_botoes, text="Verificar login", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=verificar_login,
        ).pack(fill="x", pady=2)
        botao_login = ctk.CTkButton(
            frame_botoes, text=self._texto_botao_login(perfil.id), fg_color=estilo.AZUL_MARINHO,
            hover_color=estilo.AZUL_MARINHO_HOVER, command=login_manual,
        )
        botao_login.pack(fill="x", pady=2)
        ctk.CTkButton(
            frame_botoes, text="🔑 Definir usuário/senha", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO,
            command=lambda: self._abrir_formulario_credenciais(perfil),
        ).pack(fill="x", pady=2)
        ctk.CTkButton(
            frame_botoes, text="Limpar perfil", fg_color=estilo.VERMELHO_ERRO, hover_color="#96281F",
            command=limpar_perfil,
        ).pack(fill="x", pady=2)

        self.cartoes_widgets[perfil.id] = {
            "apelido": rotulo_apelido, "email": rotulo_email, "badge": badge_status,
            "credenciais": rotulo_credenciais, "botao_login": botao_login,
        }
        return cartao

    @staticmethod
    def _texto_badge(status):
        return "Logado" if status == "Logado" else "sem login salvo"

    @staticmethod
    def _cor_badge(status):
        return estilo.VERDE_SUCESSO if status == "Logado" else estilo.AMARELO_ALERTA

    @staticmethod
    def _texto_credenciais(perfil_id):
        import credenciais as credenciais_mod
        return "🔑 Login automático configurado" if credenciais_mod.tem_credenciais(perfil_id) else "🔒 Login automático ainda não configurado"

    @staticmethod
    def _cor_credenciais(perfil_id):
        import credenciais as credenciais_mod
        return estilo.VERDE_SUCESSO if credenciais_mod.tem_credenciais(perfil_id) else estilo.TEXTO_SECUNDARIO

    @staticmethod
    def _texto_botao_login(perfil_id):
        import credenciais as credenciais_mod
        return "Entrar (login automático)" if credenciais_mod.tem_credenciais(perfil_id) else "Login manual"

    def _mostrar_aviso(self, titulo, mensagem):
        janela = ctk.CTkToplevel(self)
        janela.title(titulo)
        janela.geometry("440x200")
        janela.configure(fg_color=estilo.FUNDO_CARTAO)
        ctk.CTkLabel(
            janela, text=mensagem, font=(estilo.FONTE_PADRAO, estilo.FONTE_TEXTO_TAMANHO),
            text_color=estilo.TEXTO_PRIMARIO, wraplength=380, justify="left",
        ).pack(padx=20, pady=20)
        ctk.CTkButton(
            janela, text="Entendi", fg_color=estilo.AZUL_MARINHO, hover_color=estilo.AZUL_MARINHO_HOVER,
            command=janela.destroy,
        ).pack(pady=10)

    def _abrir_formulario_credenciais(self, perfil):
        """Formulário pra digitar usuário/senha DIRETO no app — sem abrir o
        navegador nem interagir com a tela de login. Salva no cofre do
        Windows na hora; da próxima execução em diante, o login já sai
        automático (garantir_login_para_execucao usa essas credenciais)."""
        if browser_manager.perfil_tem_navegador_aberto(perfil.id):
            self._mostrar_aviso(
                "Janela já aberta",
                f"Feche a janela de login aberta do perfil '{perfil.apelido}' antes de definir "
                "usuário/senha manualmente.",
            )
            return

        janela = ctk.CTkToplevel(self)
        janela.title(f"Definir usuário/senha — {perfil.apelido}")
        janela.geometry("420x300")
        janela.configure(fg_color=estilo.FUNDO_CARTAO)

        ctk.CTkLabel(
            janela, text="Usuário e senha da Plataforma Kroton",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_SUBTITULO_TAMANHO, "bold"), text_color=estilo.TEXTO_PRIMARIO,
        ).pack(padx=20, pady=(20, 4), anchor="w")
        ctk.CTkLabel(
            janela,
            text="Salvo direto no cofre de credenciais do Windows — não fica em nenhum "
                 "arquivo do programa. Da próxima vez, o login já sai automático.",
            font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO), text_color=estilo.TEXTO_SECUNDARIO,
            wraplength=380, justify="left",
        ).pack(padx=20, pady=(0, 16), anchor="w")

        ctk.CTkLabel(janela, text="Usuário", text_color=estilo.TEXTO_PRIMARIO).pack(padx=20, anchor="w")
        entrada_usuario = ctk.CTkEntry(janela, width=380)
        entrada_usuario.pack(padx=20, pady=(2, 12))
        entrada_usuario.focus()

        ctk.CTkLabel(janela, text="Senha", text_color=estilo.TEXTO_PRIMARIO).pack(padx=20, anchor="w")
        entrada_senha = ctk.CTkEntry(janela, width=380, show="•")
        entrada_senha.pack(padx=20, pady=(2, 4))

        rotulo_erro = ctk.CTkLabel(janela, text="", text_color=estilo.VERMELHO_ERRO, font=(estilo.FONTE_PADRAO, estilo.FONTE_PEQUENA_TAMANHO))
        rotulo_erro.pack(padx=20, anchor="w")

        def salvar():
            usuario = entrada_usuario.get().strip()
            senha = entrada_senha.get()
            if not usuario or not senha:
                rotulo_erro.configure(text="Preencha usuário e senha.")
                return
            ok = credenciais_mod.salvar_credenciais(perfil.id, usuario, senha)
            if not ok:
                rotulo_erro.configure(text="Não foi possível salvar no cofre do Windows.")
                return
            self.app.gerenciador_perfis.atualizar_apelido(perfil.id, usuario, personalizado=True)
            self._atualizar_cartao(perfil.id)
            janela.destroy()

        frame_botoes_form = ctk.CTkFrame(janela, fg_color="transparent")
        frame_botoes_form.pack(pady=16)
        ctk.CTkButton(
            frame_botoes_form, text="Salvar", fg_color=estilo.AZUL_MARINHO, hover_color=estilo.AZUL_MARINHO_HOVER,
            command=salvar,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            frame_botoes_form, text="Cancelar", fg_color=estilo.FUNDO_SECUNDARIO, hover_color=estilo.BORDA,
            text_color=estilo.TEXTO_PRIMARIO, command=janela.destroy,
        ).pack(side="left", padx=6)

        janela.bind("<Return>", lambda e: salvar())

    def _atualizar_cartao(self, perfil_id):
        perfil = self.app.gerenciador_perfis.obter(perfil_id)
        widgets = self.cartoes_widgets.get(perfil_id)
        if not perfil or not widgets:
            return
        widgets["apelido"].configure(text=perfil.apelido)
        widgets["email"].configure(text=f"E-mail: {perfil.email or 'ainda não detectado'}")
        widgets["badge"].configure(text=self._texto_badge(perfil.status), fg_color=self._cor_badge(perfil.status))
        widgets["credenciais"].configure(
            text=self._texto_credenciais(perfil_id), text_color=self._cor_credenciais(perfil_id)
        )
        if widgets.get("botao_login"):
            widgets["botao_login"].configure(text=self._texto_botao_login(perfil_id))

    def ao_exibir(self):
        for perfil in self.app.gerenciador_perfis.perfis:
            self._atualizar_cartao(perfil.id)
