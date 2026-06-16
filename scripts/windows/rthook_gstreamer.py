# PyInstaller runtime hook: point GStreamer and GObject-Introspection at the
# libraries we bundled into the frozen application.
#
# This runs *before* `import gi` / `Gst.init()` in the frozen app, so the
# environment is set up by the time the GStreamer backend starts. Paths mirror
# the layout produced by linux-show-player.spec.

import os
import sys

# In a one-dir build sys._MEIPASS is the bundle root; fall back to the exe dir.
_bundle = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))

_gst_plugins = os.path.join(_bundle, "gstreamer-1.0", "plugins")
_gi_typelibs = os.path.join(_bundle, "gi_typelibs")

# GStreamer plugin discovery (the *.dll scanners under lib/gstreamer-1.0).
os.environ["GST_PLUGIN_PATH"] = _gst_plugins
os.environ["GST_PLUGIN_SYSTEM_PATH"] = _gst_plugins
# Keep a writable, app-local registry so we don't touch the user profile.
os.environ.setdefault(
    "GST_REGISTRY", os.path.join(_bundle, "gst-registry.bin")
)
# Don't let a system GStreamer install leak into the frozen app.
os.environ["GST_PLUGIN_PATH_1_0"] = _gst_plugins

# GObject-Introspection typelibs (Gst-1.0.typelib, GstAudio-1.0.typelib, ...).
if os.path.isdir(_gi_typelibs):
    os.environ["GI_TYPELIB_PATH"] = _gi_typelibs

# Make sure the bundled DLLs (GStreamer core, glib, etc.) are on the loader path.
if hasattr(os, "add_dll_directory") and os.path.isdir(_bundle):
    try:
        os.add_dll_directory(_bundle)
    except (OSError, FileNotFoundError):
        pass
