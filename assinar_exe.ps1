# assinar_exe.ps1
# Assina dist\CapturaMensalidade.exe com o certificado gerado por
# gerar_certificado.ps1. Roda automaticamente a partir do build_exe.bat.

$ErrorActionPreference = "Stop"

$pastaCertificado = Join-Path $PSScriptRoot "certificado"
$caminhoPfx = Join-Path $pastaCertificado "CapturaMensalidade.pfx"
$caminhoSenha = Join-Path $pastaCertificado "senha.local"
$caminhoExe = Join-Path $PSScriptRoot "dist\CapturaMensalidade.exe"

if (-not (Test-Path $caminhoPfx)) {
    Write-Host "Certificado nao encontrado em $caminhoPfx. Rode gerar_certificado.ps1 primeiro."
    exit 1
}
if (-not (Test-Path $caminhoExe)) {
    Write-Host "Executavel nao encontrado em $caminhoExe. Rode o build primeiro."
    exit 1
}

$senhaSegura = Get-Content $caminhoSenha | ConvertTo-SecureString

$assinaturaExistente = Get-PfxCertificate -FilePath $caminhoPfx
$cert = Import-PfxCertificate -FilePath $caminhoPfx -CertStoreLocation "Cert:\CurrentUser\My" -Password $senhaSegura

Set-AuthenticodeSignature -FilePath $caminhoExe -Certificate $cert -TimestampServer "http://timestamp.digicert.com" | Out-Null

Write-Host "Executavel assinado com sucesso: $caminhoExe"
