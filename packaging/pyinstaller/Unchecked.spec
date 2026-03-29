# PyInstaller build spec for a one-click Windows package.

from pathlib import Path


project_root = Path(SPECPATH).resolve().parents[1]
game_dir = project_root / "game"
assets_dir = game_dir / "assets"


a = Analysis(
    ["game/main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(assets_dir), "game/assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Unchecked",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Unchecked",
)
