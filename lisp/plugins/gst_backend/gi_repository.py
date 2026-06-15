"""Utility module for importing and checking gi.repository packages once"""

import gi

try:
    gi.require_version("Gst", "1.0")
    gi.require_version("GstController", "1.0")
    gi.require_version("GstPbutils", "1.0")
    gi.require_version("GstApp", "1.0")

    # noinspection PyUnresolvedReferences
    from gi.repository import (
        GObject,
        GLib,
        Gst,
        GstController,
        GstPbutils,
        GstApp,
    )
except (ImportError, ValueError) as error:
    # ValueError: a required GStreamer namespace/version is missing.
    # ImportError: the gi.repository bindings could not be loaded.
    # Turn the cryptic gi error into a clear, actionable message instead of an
    # opaque stack trace. Bundling/installation is covered in 04_packaging.md.
    raise ImportError(
        "GStreamer 1.0 and its GObject-Introspection typelibs are required "
        "but could not be loaded. Install GStreamer 1.0 with the base and "
        "good plugin sets for your platform, then restart the application."
    ) from error
