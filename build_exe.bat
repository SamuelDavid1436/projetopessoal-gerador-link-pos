@echo off
setlocal

echo ===================================================
echo  Captura de Mensalidade - Pos Graduacao - Build do .exe
echo ===================================================

echo.
echo [1/4] Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/4] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/4] Gerando executavel com PyInstaller...
pyinstaller CapturaMensalidade.spec

if not exist dist\CapturaMensalidade.exe (
    echo ERRO: build falhou, executavel nao foi gerado.
    exit /b 1
)

echo.
echo [4/4] Verificando certificado de assinatura...
if exist certificado\CapturaMensalidade.pfx (
    echo Certificado encontrado. Assinando executavel...
    powershell -ExecutionPolicy Bypass -File assinar_exe.ps1
) else (
    echo Nenhum certificado encontrado em certificado\CapturaMensalidade.pfx
    echo O executavel nao sera assinado. Rode gerar_certificado.ps1 se desejar assinar.
)

echo.
echo Build concluido. Executavel em: dist\CapturaMensalidade.exe
endlocal
