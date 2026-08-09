# gerar_certificado.ps1
# Gera um certificado de assinatura de código autoassinado.
# Rodar UMA VEZ, na máquina de build (não nas máquinas finais).

$ErrorActionPreference = "Stop"

$nomeCertificado = "CapturaMensalidade"
$assunto = "CN=CapturaMensalidade, O=SuaEmpresa, C=BR"
$pastaSaida = Join-Path $PSScriptRoot "certificado"
$caminhoPfx = Join-Path $pastaSaida "$nomeCertificado.pfx"
$caminhoCer = Join-Path $pastaSaida "$nomeCertificado.cer"

New-Item -ItemType Directory -Force -Path $pastaSaida | Out-Null

Write-Host "Gerando certificado autoassinado..."
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $assunto `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable `
    -KeyUsage DigitalSignature `
    -KeyAlgorithm RSA `
    -KeyLength 2048 `
    -NotAfter (Get-Date).AddYears(5)

# Senha gerada localmente só para proteger o arquivo .pfx em repouso.
# O usuário final NUNCA precisa dela (instalar_certificado.ps1 não pede senha).
$senha = ConvertTo-SecureString -String ([guid]::NewGuid().ToString("N")) -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath $caminhoPfx -Password $senha | Out-Null
Export-Certificate -Cert $cert -FilePath $caminhoCer | Out-Null

# Guarda a senha localmente (fora do controle de versão) para uso do assinar_exe.ps1
Set-Content -Path (Join-Path $pastaSaida "senha.local") -Value ($senha | ConvertFrom-SecureString)

Write-Host "Certificado gerado em: $caminhoPfx"
Write-Host "Certificado publico (.cer) em: $caminhoCer"
Write-Host "Distribua o .cer (nunca o .pfx) para instalar_certificado.ps1 nas maquinas finais."
