# -*- coding: utf-8 -*-
"""
config.py
Constantes gerais, caminhos, URLs e seletores usados pela automação.
Nada de lógica de negócio aqui — só dados de configuração.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Metadados do app
# ---------------------------------------------------------------------------
NOME_APP = "Captura de Mensalidade - Pós Graduação"
NOME_APP_LINHA1 = "Captura de"
NOME_APP_LINHA2 = "Mensalidade"
NOME_APP_SUBTITULO = "Automação para consulta\ne geração de links de pagamento"
VERSAO_APP = "1.0.0"

# ---------------------------------------------------------------------------
# Caminhos base
# ---------------------------------------------------------------------------
def _base_dir():
    """Diretório base do executável/script (compatível com PyInstaller)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _base_dir()

# Dados de perfil do Chrome NUNCA em Documentos/OneDrive — só em LOCALAPPDATA,
# pra evitar corrupção de perfil por sincronização concorrente.
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
DIR_PERFIS_CHROME = os.path.join(LOCALAPPDATA, "CapturaMensalidadePosGraduacao", "PerfisChrome")

DIR_DADOS_APP = os.path.join(BASE_DIR, "dados_perfis")
DIR_SAIDA = os.path.join(BASE_DIR, "saida")
DIR_LOGS = os.path.join(BASE_DIR, "logs")
DIR_SCREENSHOTS = os.path.join(DIR_LOGS, "screenshots")
DIR_ASSETS = os.path.join(BASE_DIR, "assets")

ARQ_PERFIS = os.path.join(DIR_DADOS_APP, "perfis.json")
ARQ_HISTORICO = os.path.join(DIR_DADOS_APP, "historico.json")
ARQ_RECUPERACAO = os.path.join(DIR_DADOS_APP, "recuperacao.json")
ARQ_CONFIG_USUARIO = os.path.join(DIR_DADOS_APP, "config_usuario.json")
ARQ_ESTATISTICAS = os.path.join(DIR_LOGS, "log_processamento.json")

# ---------------------------------------------------------------------------
# Contato de suporte (ajuste para os dados reais da sua equipe)
# ---------------------------------------------------------------------------
SUPORTE_TELEFONE = "(11) 0000-0000"
SUPORTE_EMAIL = "suporte@empresa.com.br"

for _d in (DIR_PERFIS_CHROME, DIR_DADOS_APP, DIR_SAIDA, DIR_LOGS, DIR_SCREENSHOTS, DIR_ASSETS):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------------------
# URLs do sistema alvo (Plataforma Kroton / ERP)
# ---------------------------------------------------------------------------
URL_LOGIN = "https://kroton.platosedu.io/erp/login/auth"
URL_HOME = "https://kroton.platosedu.io/erp/"
URL_MATRICULA_SHOW = "https://kroton.platosedu.io/erp/matricula/show"
URL_EXTRATO_BASE = "https://kroton.platosedu.io/erp/financeiro/extratoLancamentoContabilAluno/index"

MAX_POR_PAGINA_EXTRATO = 12  # "max=12" usado pela paginação do extrato

# ---------------------------------------------------------------------------
# Seletores CSS/XPath do sistema alvo
# ---------------------------------------------------------------------------
SEL_CAMPO_BUSCA_MATRICULA = "#matriculaSearch-selectized"
SEL_DROPDOWN_OPCOES = "div.selectize-dropdown-content div[data-selectable]"
SEL_BOTAO_EXTRATO_ALUNO = "a[href*='extratoLancamentoContabilAluno/index']"
SEL_TABELA_EXTRATO = "table.table.table-hover"
SEL_LINHAS_TABELA = "table.table.table-hover tbody tr"
SEL_PAGINACAO = "ul.pagination li a.page-link"
SEL_BOTAO_ACOES_LINHA = "button.btn-actions"
SEL_LINK_GERAR = "a.dropdown-item[target='_blank']"
SEL_INPUT_LINK_PAGAMENTO = "#paymentLinkInput"

# Bloco de dados pessoais na página de extrato
SEL_BLOCO_DADOS_PESSOAIS = "div.row"  # refinado via texto em crm_client.py

# ---------------------------------------------------------------------------
# Seletores de login Microsoft (detecção de e-mail no login do perfil, caso
# o usuário escolha "Entrar com SSO (Azure AD)")
# ---------------------------------------------------------------------------
SEL_CAMPO_EMAIL_LOGIN = "input[type='email'], input[name='loginfmt'], #i0116"

# ---------------------------------------------------------------------------
# Seletores do formulário de login NATIVO da Plataforma Kroton
# (usuário/senha, em https://kroton.platosedu.io/erp/login/auth)
# ---------------------------------------------------------------------------
SEL_FORM_LOGIN = "#formLogin"
SEL_CAMPO_USUARIO = "#usuario"
SEL_CAMPO_SENHA = "#password"
SEL_BOTAO_ENTRAR = "#formLogin button[type='submit']"

# ---------------------------------------------------------------------------
# Parâmetros de execução / robustez
# ---------------------------------------------------------------------------
TIMEOUT_PADRAO = 20          # segundos, espera adaptativa padrão
TIMEOUT_LONGO = 40           # páginas mais pesadas / grades grandes
MAX_TENTATIVAS_SESSAO = 3    # reinícios de navegador por perfil
MAX_TENTATIVAS_ITEM = 3      # retries por item em caso de timeout
ZOOM_REDUZIDO = "67%"        # aplicado quando a grade é larga/virtualizada

# Regex do padrão de parcela de mensalidade elegível para link
# Ex.: "2a. Parcela de Mensalidade JULHO/2026 (2/18)"
REGEX_PARCELA_MENSALIDADE = r"Parcela de Mensalidade\s+([A-ZÇÃÕ]+)/(\d{4})\s*\((\d+)/(\d+)\)"

SITUACAO_ELEGIVEL_LINK = "Em aberto"

MESES_PT = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "ABRIL": 4,
    "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9,
    "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}

# ---------------------------------------------------------------------------
# Colunas do arquivo de saída
# ---------------------------------------------------------------------------
COLUNAS_ENTRADA_OBRIGATORIAS = ["CPF"]

# Formato "longo" (uma linha por parcela) — usado internamente pelo runner
# e disponível como arquivo de detalhe (resultado_detalhado.csv/.xlsx).
COLUNAS_SAIDA = [
    "CPF",
    "Nome",
    "Situacao_Matricula",
    "Curso",
    "Plano",
    "Email",
    "Mes_Ano",
    "Valor_Pago",
    "Situacao_Parcela",
    "Link_Pagamento",
    "Status_Processamento",
    "Observacao",
]

# Formato "largo" (uma linha por CPF, com colunas fixas por mês do
# calendário) — é o arquivo de saída principal (resultado.csv/.xlsx).
COLUNAS_BASE_SAIDA_LARGA = [
    "CPF",
    "Nome",
    "Situacao_Matricula",
    "Curso",
    "Plano",
    "Email",
    "Status_Processamento",
    "Observacao",
]

# Janela fixa de colunas por mês: sempre de Junho a Dezembro do ano
# definido, na mesma ordem/posição pra todo mundo — dá pra comparar entre
# alunos diretamente. Ajuste aqui se precisar mudar o intervalo no futuro.
ANO_SAIDA = 2026
MESES_SAIDA_ORDENADOS = [
    "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
MESES_SAIDA_NUMERO = {
    "Junho": 6, "Julho": 7, "Agosto": 8, "Setembro": 9,
    "Outubro": 10, "Novembro": 11, "Dezembro": 12,
}

TEXTO_COM_MENSALIDADE = "Com mensalidade"
TEXTO_SEM_MENSALIDADE = "Sem mensalidade"

# Corte de colunas por competência: mantido por compatibilidade com o
# formato longo/detalhado — nenhuma competência posterior a este mês/ano
# entra no arquivo detalhado.
CORTE_COLUNAS_ANO = 2026
CORTE_COLUNAS_MES = 12

MSG_NAO_ENCONTRADO = "CPF não encontrado na Plataforma Kroton"
