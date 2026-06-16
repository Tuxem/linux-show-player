# Windows build pipeline

Builds a frozen, self-contained Windows distribution of Linux Show Player
(`.exe` one-dir bundle + Inno Setup installer), **GStreamer included**, so end
users install nothing else.

This directory is additive and isolated: it touches neither the runtime code
nor `scripts/flatpak/`. See `docs/cross-platform/04_packaging.md` (PR-C).

## Files

| File | Role |
|------|------|
| `build.ps1` | One-shot build: venv, GStreamer, PyGObject, PyInstaller, installer. |
| `linux-show-player.spec` | PyInstaller spec (bundles `lisp/`, GStreamer, Qt). |
| `entry.py` | Frozen entry point → `lisp.main:main`. |
| `rthook_gstreamer.py` | Runtime hook wiring `GST_PLUGIN_PATH` / `GI_TYPELIB_PATH`. |
| `installer.iss` | Inno Setup installer script. |
| `requirements-windows.txt` | Cross-platform deps only (no jack/pyalsa/pyliblo3). |

## Two ways to build

### 1. CI (recommended, dev-machine independent)

`PyInstaller cannot cross-compile`: a Windows `.exe` must be built **on**
Windows. Our reproducible "container" is therefore the GitHub Actions
`windows-latest` runner — an ephemeral, identical-for-everyone environment, not
anyone's laptop. The `build-windows` job in `.github/workflows/ci.yml`:

* runs `build.ps1` per architecture (matrix → parallel builds),
* smoke-tests the produced `.exe` (`--help`, offscreen),
* uploads the installer + bundle as a downloadable artifact.

Push the branch and grab the artifact from the Actions run — no local Windows
needed to *produce* a build.

### 2. Local, on a physical Windows machine

Use this for the **real audio/MIDI test** (manual checklist, level 4 of
`docs/cross-platform/05_test_strategy.md`) — CI cannot exercise real sound.

Prerequisites: Python 3.11 (x64), and optionally
[Inno Setup 6](https://jrsoftware.org/isdl.php) on `PATH` (for the installer).

```powershell
# From the repo root, in PowerShell:
pwsh scripts/windows/build.ps1                       # x86_64, default GStreamer
pwsh scripts/windows/build.ps1 -GstVersion 1.24.13   # pin GStreamer
pwsh scripts/windows/build.ps1 -SkipInstaller        # bundle only
```

Outputs under `build/windows/`:
* `dist/LinuxShowPlayer/LinuxShowPlayer.exe` — runnable bundle,
* `installer/LinuxShowPlayer-<version>-setup.exe` — installer.

## Multi-architecture / parallelism

* The CI `matrix` builds architectures concurrently (one runner each). Add
  `arm64` (runner `windows-11-arm`) to the `include:` list once a GStreamer
  arm64 Windows runtime is published — `build.ps1 -Arch arm64` already handles
  the MSI/path logic.
* `build.ps1` exports `MAKEFLAGS=-j<NUMBER_OF_PROCESSORS>` so any native wheel
  compilation uses all cores. PyInstaller's own analysis is single-threaded by
  design.

## How GStreamer is bundled

GStreamer is **not** pip-installable. `build.ps1` silently installs the
official MSVC **runtime + devel** MSIs (`ADDLOCAL=ALL` → all plugin sets), which
land in `C:\gstreamer\1.0\msvc_<arch>`. The spec then copies, from that root:

* `bin\*.dll` → bundle root (GStreamer core + glib),
* `lib\gstreamer-1.0\*.dll` → `gstreamer-1.0/plugins/`,
* `lib\girepository-1.0\*.typelib` → `gi_typelibs/`.

`rthook_gstreamer.py` points GStreamer/GI at those bundled dirs before
`Gst.init()`. PyGObject is built against the devel package's `pkg-config`
(hence installed *after* GStreamer, not via the requirements file).

## Why the whole `lisp/` tree ships as data

The plugin / GStreamer-element / theme loaders discover modules by
`os.scandir()`-ing each package directory (`lisp/core/loading.py`). Frozen
modules live in the PYZ archive, **not on disk**, so that scan would come up
empty. The spec therefore ships the `lisp/` source tree as on-disk data *and*
collects its submodules as hidden imports. If you add a plugin and it isn't
discovered in the frozen build, this is the first place to look.

## Known rough edges (expect iteration on a real machine)

* **GStreamer bundling** is the most fragile step — a missing plugin shows up
  only at runtime. After building, verify audio playback against the manual
  checklist; if a format fails, confirm its plugin DLL is under
  `gstreamer-1.0/plugins/`.
* **Code signing** (Authenticode) is not wired in. Unsigned installers trigger
  SmartScreen warnings. Add signing once a certificate is available.
* **App icon**: drop an `app.ico` in this folder and the spec/installer will
  pick it up automatically.
