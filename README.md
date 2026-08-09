# Captura de Mensalidade — Pós Graduação

![logo](assets/logo.png)

Automação (Python + Selenium + interface gráfica) que localiza um aluno
pelo CPF na Plataforma Kroton, extrai os dados pessoais e o extrato de
lançamentos, e gera automaticamente o link de pagamento das parcelas de
mensalidade em aberto do mês anterior, do mês vigente e do mês seguinte.

Interface e arquitetura fiéis ao projeto de referência interno (perfis,
runner, histórico, recuperação de erro, empacotamento), com paleta
própria em tons de azul marinho e dourado sobre tema claro.

## Requisitos

- Windows 10/11
- Python 3.11+ (para rodar a partir do código-fonte)
- Google Chrome instalado
- ChromeDriver compatível com a versão do Chrome instalado (o Selenium
  Manager, incluso no Selenium 4.20+, baixa automaticamente)

## Rodando a partir do código-fonte

```bat
pip install -r requirements.txt
python main.py
```

## Estrutura do projeto

```
main.py                    Ponto de entrada
app_gui.py                  Controlador principal + navegação
browser_manager.py          Gestão de perfis do Chrome (login independente)
crm_client.py                Automação Selenium do fluxo Kroton
runner.py                    Orquestração de workers em paralelo
perfis.py                     Metadados persistidos de cada perfil
history.py                    Histórico de execuções
estatisticas.py                Estatísticas persistentes do painel (Início)
recuperacao.py                 Log de retomada em caso de queda
data_io.py                     Leitura da base de entrada / gravação de saída
config.py                      URLs, seletores, caminhos, constantes
estilo.py                      Paleta de cores (tema claro, azul marinho)
paginas/                       Uma página por tela (Início, Perfis, etc.)
assets/                        Ícone (.ico), logo (.png), manual (Word + PDF)
gerar_identidade_visual.py     Script que gera o ícone e a logo do app
```

## Identidade visual

O ícone (`assets/icone.ico`) e a logo horizontal (`assets/logo.png`) já
vêm prontos no projeto. Se quiser regerar (por exemplo, após ajustar
cores em `estilo.py`), rode:

```bat
python gerar_identidade_visual.py
```

## Perfis (até 3 logins independentes)

Cada perfil abre o Chrome com seu próprio `--user-data-dir`, guardado em
`%LOCALAPPDATA%\CapturaMensalidadePosGraduacao\PerfisChrome\perfil_N` —
nunca em Documentos/OneDrive, para evitar corrupção por sincronização
concorrente.

**Login automático com credenciais salvas.** Na primeira vez, clique em
"Login manual" e digite usuário e senha na tela nativa da Plataforma
Kroton (`kroton.platosedu.io/erp/login/auth`). Assim que o login é
confirmado (redirecionamento pra fora da tela de login), o app:
- salva usuário e senha no **cofre de credenciais do sistema
  operacional** (Windows Credential Manager, via a biblioteca `keyring`)
  — nunca em texto puro em nenhum arquivo do projeto;
- atualiza o apelido do perfil para o usuário digitado;
- fecha a janela sozinho, liberando a pasta do perfil.

Da próxima vez, o botão vira **"Entrar (login automático)"** — clique e
ele preenche e envia o formulário de login sozinho, sem digitação manual.
O mesmo login automático é usado internamente antes de qualquer execução
(`runner.py` chama `browser_manager.garantir_login_para_execucao()`), e
**nenhum CPF é processado até o login ser confirmado** — evita uma
cascata de erros logo no primeiro item caso a sessão tenha expirado.

Use "Verificar login" para checar se a sessão ainda está válida sem abrir
uma janela visível, e "Limpar perfil" para resetar tudo daquele perfil
(pasta do Chrome + apelido + e-mail + **credenciais salvas**).

> Todo esse fluxo — abrir uma segunda janela do Chrome pro mesmo perfil
> enquanto a primeira ainda está aberta — é bloqueado pelo app
> (`browser_manager.PerfilEmUsoError`), porque o Chrome não permite dois
> processos disputando a mesma pasta de perfil ao mesmo tempo (isso é o
> que historicamente fazia o login "não salvar de verdade").

## Base de entrada

CSV ou Excel com uma coluna de **CPF** (com ou sem cabeçalho). O separador
do CSV é detectado automaticamente (não usamos `sep=None` do pandas, que
trunca valores numéricos em arquivos sem cabeçalho).

## Saída

Cada execução gera sua própria pasta em `saida/AAAA-MM-DD_HH-MM-SS/`, com:

- **`resultado.csv` / `resultado.xlsx`** (arquivo principal — separador
  `;`, `utf-8-sig`): **uma linha por CPF**, com colunas fixas por mês do
  calendário — sempre `Junho` a `Dezembro` de `config.ANO_SAIDA` (2026 por
  padrão), na mesma posição em toda linha, pra dar pra comparar entre
  alunos diretamente. Colunas base: CPF, Nome, Situação da Matrícula,
  Curso, Plano, Email, Status do Processamento, Observação. Pra cada mês
  da janela: `{Mês} - Situação` ("Com mensalidade" / "Sem mensalidade"),
  `{Mês} - Valor Pago` e `{Mês} - Link Pagamento`. Competências fora da
  janela Junho–Dezembro do ano configurado são ignoradas nesse arquivo
  (ficam registradas no detalhado). Se quiser mudar o intervalo de meses,
  ajuste `ANO_SAIDA`/`MESES_SAIDA_ORDENADOS` em `config.py`.
- **`resultado_detalhado.csv` / `resultado_detalhado.xlsx`**: formato
  longo (uma linha por parcela), útil pra auditoria/depuração. Colunas:
  CPF, Nome, Situação da Matrícula, Curso, Plano, Email, Mês/Ano, Valor
  Pago, Situação da Parcela, Link de Pagamento, Status do Processamento,
  Observação.
- **`reprocessar_erros.xlsx`**: só os CPFs que deram erro, pronto pra
  reimportar.

## Painel (tela Início)

- **Dados Capturados (histórico total)**: contador persistente, nunca
  reseta sozinho — só pelo botão "Zerar estatísticas do painel" em
  Configurações.
- **Perfis Selecionados**: quantidade de perfis atualmente logados.
- **Execuções Hoje** / **Tempo Total Hoje**: calculados a partir do
  histórico de execuções filtrado pela data de hoje.

## Tratamento de erros

- Toda consulta com erro salva um screenshot automático em
  `logs/screenshots/`.
- CPF não encontrado gera a mensagem "CPF não encontrado na Plataforma
  Kroton".
- Se o programa cair no meio de uma execução, ao reabrir ele oferece
  recuperar os resultados parciais.
- Se campos pessoais importantes (Nome, Email) vierem vazios sem erro
  explícito, a linha é marcada com um aviso na coluna Observação.

## Empacotamento (.exe)

Veja `LEIAME_EMPACOTAMENTO.md` para o passo a passo completo de build e
assinatura, e `TI_LEIA_ISTO.md` para instruções de liberação nas máquinas
finais.

---

*Adaptado da arquitetura interna de automação de captura de dados,
testada em produção.*
