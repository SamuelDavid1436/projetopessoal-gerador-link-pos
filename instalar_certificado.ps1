# instalar_certificado.ps1
# Roda UMA VEZ em cada máquina final (sem domínio/AD) para que o Windows
# passe a confiar no certificado autoassinado usado para assinar o .exe.
# Não pede senha nenhuma ao usuário final — usa só o certificado público (.cer).

$ErrorActionPreference = "Stop"

$caminhoCer = Join-Path $PSScriptRoot "certificado\CapturaMensalidade.cer"

if (-not (Test-Path $caminhoCer)) {
    Write-Host "Arquivo de certificado nao encontrado: $caminhoCer"
    Write-Host "Copie o CapturaMensalidade.cer para esta pasta antes de rodar este script."
    exit 1
}

Write-Host "Instalando certificado como confiavel (Raizes de Certificacao Confiaveis)..."
Import-Certificate -FilePath $caminhoCer -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null

Write-Host "Instalando certificado como confiavel (Editores Confiaveis)..."
Import-Certificate -FilePath $caminhoCer -CertStoreLocation "Cert:\LocalMachine\TrustedPublisher" | Out-Null

Write-Host "Certificado instalado com sucesso. O executavel assinado agora sera reconhecido como confiavel."
