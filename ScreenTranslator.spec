# -*- mode: python ; coding: utf-8 -*-
import glob
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

SPEC_DIR = os.path.abspath(SPECPATH)
SP = os.path.join(sys.prefix, "Lib", "site-packages")

# RapidOCR 的 onnx 模型与配置；连 .py 一起带上，是因为它会把自己的目录塞进 sys.path，
# 然后按顶级名 importlib.import_module("ch_ppocr_v3_det") 导入子包——
# 单文件模式下若磁盘上没有真实 .py，Python 只会得到空命名空间包。
datas = collect_data_files(
    "rapidocr_onnxruntime",
    include_py_files=True,
    excludes=["**/__pycache__", "**/*.pyc"],
)

binaries = []
# onnxruntime 原生库（保留原始相对目录，运行时按同目录查找）
binaries += collect_dynamic_libs("onnxruntime")
# ctranslate2：CPU 推理只需要主库 + OpenMP，跳过 CUDA/cudnn 相关
for src, dest in collect_dynamic_libs("ctranslate2"):
    if "cudnn" in os.path.basename(src).lower() or "cublas" in os.path.basename(src).lower():
        continue
    binaries.append((src, dest))
# shapely 的 GEOS 原生库在同级 shapely.libs 目录里
for dll in glob.glob(os.path.join(SP, "shapely.libs", "*.dll")):
    binaries.append((dll, "shapely.libs"))

excludes = [
    "tkinter", "unittest", "pydoc", "doctest", "pytest", "IPython",
    "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets", "PyQt6.QtWebEngineQuick",
    "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtQuickWidgets", "PyQt6.QtQuick3D",
    "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets", "PyQt6.QtCharts",
    "PyQt6.Qt3DCore", "PyQt6.QtBluetooth", "PyQt6.QtNfc", "PyQt6.QtPositioning",
    "PyQt6.QtSerialPort", "PyQt6.QtSql", "PyQt6.QtTest", "PyQt6.QtDesigner",
    "PyQt5", "PySide2", "PySide6",
]

hiddenimports = [
    "ctranslate2",
    "sentencepiece",
    "mss.windows",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    # rapidocr 的三个子包是 importlib 动态导入的，静态分析抓不到，
    # 必须显式声明，否则 pyclipper / shapely 等依赖不会入包
    "pyclipper",
    "shapely.geometry",
    "six",
]
hiddenimports += collect_submodules("rapidocr_onnxruntime")

a = Analysis(
    [os.path.join(SPEC_DIR, "main.py")],
    pathex=[SPEC_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='ScreenTranslator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(SPEC_DIR, 'app.ico')],
)
