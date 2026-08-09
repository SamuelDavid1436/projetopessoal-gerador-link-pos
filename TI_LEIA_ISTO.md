# Para a equipe de TI — liberação do CapturaMensalidade.exe

Este documento resume o que a TI precisa saber para liberar o aplicativo
nas máquinas dos usuários.

## O que é

Um executável Windows (`CapturaMensalidade.exe`) que automatiza, via
Selenium + Chrome, a busca de dados de matrícula/financeiro de alunos na
Plataforma Kroton, usando o **login do próprio usuário**. Na primeira
vez, o usuário digita usuário e senha manualmente no Chrome controlado
pelo app; da segunda vez em diante, o app loga sozinho usando as
credenciais salvas (ver seção abaixo).

## Requisitos na máquina do usuário

- Windows 10/11
- Google Chrome instalado e atualizado
- Acesso de rede à Plataforma Kroton (`kroton.platosedu.io`)
- Permissão de escrita em `%LOCALAPPDATA%` (padrão para qualquer usuário)

## Liberação (uma vez por máquina)

1. Copie para a máquina: `CapturaMensalidade.exe`,
   `CapturaMensalidade.cer` e `instalar_certificado.ps1`.
2. Rode, como administrador:
   ```powershell
   powershell -ExecutionPolicy Bypass -File instalar_certificado.ps1
   ```
3. Pronto — o `.exe` assinado passa a ser reconhecido como confiável pelo
   Windows (sem o alerta padrão de "editor desconhecido/SmartScreen").

## Dados gravados localmente

- Perfis do Chrome (sessão de login): `%LOCALAPPDATA%\CapturaMensalidadePosGraduacao\PerfisChrome\`
- Resultados das execuções: pasta `saida\` ao lado do `.exe`
- Logs e screenshots de erro: pasta `logs\` ao lado do `.exe`
- **Usuário e senha de cada perfil**: salvos no **Gerenciador de
  Credenciais do Windows** (Windows Credential Manager), via a biblioteca
  `keyring` — não em nenhum arquivo do app, e nunca em texto puro. O
  cofre é gerenciado pelo próprio Windows e atrelado à conta do usuário
  logado na máquina, da mesma forma que o navegador Edge/Chrome já faz
  para senhas salvas. Para remover as credenciais de um perfil, use
  "Limpar perfil" na tela Perfis do app (isso apaga a entrada
  correspondente do cofre) — ou, manualmente, procure por
  "CapturaMensalidadePosGraduacao" no Gerenciador de Credenciais do
  Windows (Painel de Controle → Contas de Usuário → Gerenciador de
  Credenciais → Credenciais Genéricas).

## Dúvidas

Ver `README.md` (visão geral) e `LEIAME_EMPACOTAMENTO.md` (build e
assinatura) na raiz do projeto.
