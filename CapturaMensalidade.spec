# -*- mode: python ; coding: utf-8 -*-
"""
Especificação PyInstaller para o Captura de Mensalidade - Pós Graduação.
Gera um único .exe, com ícone, assets embutidos e os hidden imports
necessários para Selenium/pandas/PIL/customtkinter.
"""

import customtkinter
import os

caminho_ctk = os.path.dirname(customtkinter.__file__)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (caminho_ctk, 'customtkinter'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'pandas',
        'openpyxl',
        'PIL',
        'PIL._tkinter_finder',
        'customtkinter',
        'psutil',
        'keyring',
        'keyring.backends',
        'keyring.backends.Windows',
        'keyring.backends.chainer',
        'win32ctypes.pywin32',
        'win32timezone',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CapturaMensalidade',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icone.ico',
)
