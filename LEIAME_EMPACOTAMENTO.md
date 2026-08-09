# Empacotamento e assinatura — Captura Link de Pagamento (Kroton)

Passo a passo pra gerar o `.exe` final, assiná-lo com um certificado
autoassinado, e preparar tudo pra liberação nas máquinas finais.

## 1. Gerar o certificado (uma vez, na máquina de build)

```powershell
powershell -ExecutionPolicy Bypass -File gerar_certificado.ps1
```

Isso cria a pasta `certificado/` com:
- `CapturaMensalidade.pfx` — chave privada (NUNCA versionar, já está no `.gitignore`)
- `CapturaMensalidade.cer` — certificado público, o que você distribui
- `senha.local` — senha do `.pfx`, usada só localmente pelo `assinar_exe.ps1`

## 2. Buildar e assinar

```bat
build_exe.bat
```

O script:
1. Instala as dependências de `requirements.txt` + PyInstaller
2. Limpa builds anteriores (`build/`, `dist/`)
3. Roda o PyInstaller com `CapturaMensalidade.spec`
4. Se encontrar `certificado/CapturaMensalidade.pfx`, assina automaticamente
   o `.exe` gerado

O executável final fica em `dist/CapturaMensalidade.exe`.

## 3. Distribuir para as máquinas finais

Você precisa levar para cada máquina final:
- `dist/CapturaMensalidade.exe`
- `certificado/CapturaMensalidade.cer` (certificado **público**, não o `.pfx`)
- `instalar_certificado.ps1`

Nas máquinas finais, rode uma vez (como administrador):

```powershell
powershell -ExecutionPolicy Bypass -File instalar_certificado.ps1
```

Isso instala o certificado como confiável no Windows, sem pedir nenhuma
senha ao usuário final. Depois disso, o `.exe` assinado roda sem alertas
de "editor desconhecido".

## Notas

- Se você mudar de máquina de build ou gerar um novo certificado, é
  preciso reinstalar o `.cer` em todas as máquinas finais.
- O certificado é autoassinado — válido para ambientes sem domínio/AD.
  Em ambientes com AD, prefira distribuir via GPO.
