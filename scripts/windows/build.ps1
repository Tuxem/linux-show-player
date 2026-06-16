<#
.SYNOPSIS
    Build the Windows distribution of Linux Show Player (frozen .exe + installer).

.DESCRIPTION
    One script, two contexts:
      * Your physical Windows machine (manual build + real audio test).
      * GitHub Actions `windows-latest` runner (reproducible, dev-machine
        independent build -- this is our "build in a container" equivalent,
        since PyInstaller cannot cross-compile a Windows exe from Linux).

    Steps:
      1. Create an isolated venv and install cross-platform deps.
      2. Download + silently install the official GStreamer runtime AND devel
         packages for the requested architecture.
      3. Build PyGObject against GStreamer's pkg-config.
      4. Run PyInstaller (one-dir bundle, GStreamer bundled).
      5. Optionally build the Inno Setup installer (if ISCC is available).

.PARAMETER Arch
    Target architecture: x86_64 (default) or arm64.

.PARAMETER GstVersion
    GStreamer 1.0 version to bundle (default 1.24.12).

.PARAMETER SkipInstaller
    Build only the one-dir bundle, skip the Inno Setup step.

.EXAMPLE
    pwsh scripts/windows/build.ps1
    pwsh scripts/windows/build.ps1 -Arch x86_64 -GstVersion 1.24.12
#>
[CmdletBinding()]
param(
    [ValidateSet("x86_64", "arm64")]
    [string]$Arch = "x86_64",
    [string]$GstVersion = "1.24.13",
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Repo root = two levels up from this script.
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$BuildDir = Join-Path $RepoRoot "build\windows"
$null = New-Item -ItemType Directory -Force -Path $BuildDir

# Parallelism: PyInstaller's analysis is single-threaded, but pip wheel builds
# and the matrix in CI parallelise across cores/architectures. Surface the core
# count so any sub-tool that honours it (e.g. native wheel compiles) can use it.
$env:MAKEFLAGS = "-j$($env:NUMBER_OF_PROCESSORS)"
Write-Host "==> Building for $Arch using up to $($env:NUMBER_OF_PROCESSORS) cores"

# --- 1. Python venv ------------------------------------------------------
$VenvDir = Join-Path $BuildDir "venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "==> Creating venv at $VenvDir"
    python -m venv $VenvDir
}
$Py = Join-Path $VenvDir "Scripts\python.exe"
& $Py -m pip install --upgrade pip wheel
& $Py -m pip install -r (Join-Path $PSScriptRoot "requirements-windows.txt")

# --- 2. GStreamer runtime + devel ----------------------------------------
$GstArch = if ($Arch -eq "arm64") { "arm64" } else { "x86_64" }
# Note the /msvc subdir: the official tree is .../windows/<ver>/msvc/<file>.msi
$GstBase = "https://gstreamer.freedesktop.org/data/pkg/windows/$GstVersion/msvc"
$Runtime = "gstreamer-1.0-msvc-$GstArch-$GstVersion.msi"
$Devel   = "gstreamer-1.0-devel-msvc-$GstArch-$GstVersion.msi"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-ValidMsi($path) {
    # Authoritative check: open the package with the Windows Installer engine,
    # exactly as msiexec does. A truncated download (e.g. Ctrl-C) has a valid
    # OLE header but fails to open here -- the only reliable way to catch the
    # exit-1620 "package invalid" case without trusting Content-Length.
    if (-not (Test-Path $path)) { return $false }
    if ((Get-Item $path).Length -lt 1MB) { return $false }
    try {
        $installer = New-Object -ComObject WindowsInstaller.Installer
        # OpenDatabase mode 0 = read-only; throws if the package is invalid.
        $db = $installer.GetType().InvokeMember(
            'OpenDatabase', 'InvokeMethod', $null, $installer, @($path, 0))
        [void]$db
        return $true
    } catch {
        return $false
    } finally {
        if ($installer) {
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($installer)
        }
    }
}

function Install-Msi($url, $name) {
    $dst = Join-Path $BuildDir $name
    if (-not (Test-ValidMsi $dst)) {
        if (Test-Path $dst) {
            Write-Host "==> Cached $name is invalid/incomplete; re-downloading"
            Remove-Item $dst -Force
        }
        Write-Host "==> Downloading $name"
        Invoke-WebRequest -Uri $url -OutFile $dst -UseBasicParsing
        if (-not (Test-ValidMsi $dst)) {
            throw "Downloaded $name is not a valid MSI (corrupt/incomplete)."
        }
    }
    $log = Join-Path $BuildDir "$name.install.log"
    Write-Host "==> Installing $name (silent, full feature set)"
    # ADDLOCAL=ALL installs every plugin set (base/good/bad/libav). The MSI is a
    # per-machine install to C:\gstreamer and needs elevation; -Verb RunAs
    # prompts UAC on an interactive machine and is unnecessary on an already
    # elevated CI runner (so we only add it when not already admin). /l*v writes
    # a verbose log to diagnose any failure (exit 1603 = generic fatal error).
    $spArgs = @(
        "/i", "`"$dst`"", "/qn", "/norestart", "ADDLOCAL=ALL",
        "/l*v", "`"$log`""
    )
    $sp = @{
        FilePath     = "msiexec.exe"
        ArgumentList = $spArgs
        Wait         = $true
        PassThru     = $true
    }
    if (-not (Test-Admin)) { $sp.Verb = "RunAs" }
    $p = Start-Process @sp
    if ($p.ExitCode -ne 0) {
        Write-Warning "msiexec verbose log: $log"
        throw "msiexec failed for $name (exit $($p.ExitCode)); see log above."
    }
}

Install-Msi "$GstBase/$Runtime" $Runtime
Install-Msi "$GstBase/$Devel" $Devel

# The MSI installs to C:\gstreamer\1.0\msvc_<arch>. Expose the env vars the
# spec and PyGObject build expect.
$GstRoot = "C:\gstreamer\1.0\msvc_$GstArch"
if (-not (Test-Path $GstRoot)) {
    throw "GStreamer root not found at $GstRoot after install."
}
$env:GSTREAMER_1_0_ROOT_MSVC_X86_64 = $GstRoot
$env:PATH = "$GstRoot\bin;$env:PATH"
$env:PKG_CONFIG_PATH = "$GstRoot\lib\pkgconfig"
$env:GI_TYPELIB_PATH = "$GstRoot\lib\girepository-1.0"
Write-Host "==> GStreamer root: $GstRoot"

# --- 3. PyGObject (built against GStreamer's pkg-config) ------------------
Write-Host "==> Installing PyGObject against GStreamer pkg-config"
& $Py -m pip install pycairo
& $Py -m pip install PyGObject

# --- 4. PyInstaller ------------------------------------------------------
Write-Host "==> Running PyInstaller"
Push-Location $RepoRoot
try {
    & $Py -m PyInstaller `
        (Join-Path $PSScriptRoot "linux-show-player.spec") `
        --noconfirm `
        --distpath (Join-Path $BuildDir "dist") `
        --workpath (Join-Path $BuildDir "work")
} finally {
    Pop-Location
}

$DistApp = Join-Path $BuildDir "dist\LinuxShowPlayer"
Write-Host "==> Bundle ready: $DistApp"

# --- 5. Installer (optional) ---------------------------------------------
if ($SkipInstaller) {
    Write-Host "==> Skipping installer (--SkipInstaller)"
    return
}
$Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Iscc) {
    Write-Warning "ISCC.exe (Inno Setup) not found; skipping installer build."
    Write-Warning "Install Inno Setup 6 or re-run with -SkipInstaller."
    return
}
Write-Host "==> Building installer with Inno Setup"
& $Iscc.Source `
    "/DAppVersion=0.6.5" `
    "/DSourceDir=$DistApp" `
    "/DOutputDir=$(Join-Path $BuildDir 'installer')" `
    (Join-Path $PSScriptRoot "installer.iss")

Write-Host "==> Done. Installer in $(Join-Path $BuildDir 'installer')"
