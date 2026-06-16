# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the Windows build of Linux Show Player.
#
# Build (from the repo root, on Windows, inside the prepared venv):
#     pyinstaller scripts/windows/linux-show-player.spec --noconfirm
#
# Most callers should use scripts/windows/build.ps1, which prepares Python,
# GStreamer and PyGObject before invoking this spec.
#
# Design notes (see scripts/windows/README.md for the full story):
#  * The runtime discovers plugins / GStreamer elements / UI themes by
#    `os.scandir()`-ing the *directory* of each package (lisp/core/loading.py).
#    Frozen modules live in the PYZ archive, not on disk, so that scan would
#    find nothing. We therefore ship the whole `lisp/` source tree as on-disk
#    *data* (so scandir sees the .py files) AND collect its submodules as
#    hidden imports (so the imports resolve).
#  * GStreamer is not pip-installable: we copy its DLLs, plugins and GI
#    typelibs from the official runtime, located via the
#    GSTREAMER_1_0_ROOT_MSVC_<arch> env var set by the official installer.

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

# SPECPATH is injected by PyInstaller: scripts/windows -> repo root.
PROJECT_ROOT = Path(SPECPATH).resolve().parent.parent
HERE = Path(SPECPATH).resolve()

datas = []
binaries = []
hiddenimports = []

# --- 1. The lisp package: source on disk (for scandir) + importable modules ---
for f in (PROJECT_ROOT / "lisp").rglob("*"):
    if not f.is_file():
        continue
    if "__pycache__" in f.parts or f.suffix in (".pyc", ".pyo"):
        continue
    rel_parent = f.relative_to(PROJECT_ROOT).parent
    datas.append((str(f), str(rel_parent)))

hiddenimports += collect_submodules("lisp")

# --- 2. GObject Introspection (gi) ---------------------------------------
gi_datas, gi_binaries, gi_hidden = collect_all("gi")
datas += gi_datas
binaries += gi_binaries
hiddenimports += gi_hidden

# --- 3. GStreamer runtime (DLLs, plugins, typelibs) ----------------------
def _gst_root():
    for var in (
        "GSTREAMER_1_0_ROOT_MSVC_X86_64",
        "GSTREAMER_1_0_ROOT_MSVC_ARM64",
        "GSTREAMER_1_0_ROOT_X86_64",
        "GSTREAMER_1_0_ROOT_MINGW_X86_64",
    ):
        val = os.environ.get(var)
        if val and Path(val).is_dir():
            return Path(val)
    return None


_root = _gst_root()
if _root is not None:
    # Core GStreamer + glib DLLs live in <root>/bin.
    for dll in (_root / "bin").glob("*.dll"):
        binaries.append((str(dll), "."))
    # GStreamer plugins (lib/gstreamer-1.0/*.dll) -> bundled plugin dir.
    plugin_dir = _root / "lib" / "gstreamer-1.0"
    for dll in plugin_dir.glob("*.dll"):
        binaries.append((str(dll), "gstreamer-1.0/plugins"))
    # GI typelibs needed by the gst_backend (Gst, GstAudio, GstPbutils, ...).
    typelib_dir = _root / "lib" / "girepository-1.0"
    for tl in typelib_dir.glob("*.typelib"):
        datas.append((str(tl), "gi_typelibs"))
else:
    print(
        "WARNING: GStreamer runtime not found (set GSTREAMER_1_0_ROOT_MSVC_X86_64). "
        "The build will run but audio playback will fail at runtime."
    )

# Hidden imports that dynamic loading / optional deps can miss.
hiddenimports += [
    "gi",
    "mido.backends.rtmidi",
    "numpy",
]

# Native Linux-only bindings must never be pulled into the Windows bundle.
excludes = ["tkinter", "pyalsa", "jack", "alsaaudio"]

icon_ico = PROJECT_ROOT / "scripts" / "windows" / "app.ico"

a = Analysis(
    [str(HERE / "entry.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(HERE / "rthook_gstreamer.py")],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LinuxShowPlayer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX corrupts some Qt/GStreamer DLLs; keep it off.
    console=False,
    icon=str(icon_ico) if icon_ico.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="LinuxShowPlayer",
)
