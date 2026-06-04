# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules


datas = [
    ("bookmark_map.json", "."),
    ("ref_img.png", "."),
]
binaries = []
hiddenimports = [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "cv2",
    "mss",
    "numpy",
    "pyautogui",
    "pyperclip",
    "torch",
    "torchvision",
    "transformers",
    "timm",
    "skimage",
]

for package_name in ("rapidocr_onnxruntime", "onnxruntime"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

for package_name in ("transformers", "timm"):
    datas += collect_data_files(package_name)
    hiddenimports += collect_submodules(package_name)


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Radiology_Auto_Reporter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Radiology_Auto_Reporter",
)
