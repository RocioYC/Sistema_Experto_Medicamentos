# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Vista\\interfaz_principal.py'],
    pathex=[],
    binaries=[],
    datas=[('Modelo\\01Hechos\\clinical_data.csv', 'Modelo\\01Hechos'), ('Modelo\\BaseConocimiento\\medicamentos_info.csv', 'Modelo\\BaseConocimiento'), ('Modelo\\BaseConocimiento\\sustitutos_medicamentos.csv', 'Modelo\\BaseConocimiento'), ('Modelo\\ReglasClinicas\\posibles_alergenos.csv', 'Modelo\\ReglasClinicas')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='interfaz_principal',
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
)
