# This file is part of Linux Show Player
#
# Copyright 2026 Francesco Ceruti <ceppofrancy@gmail.com>
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

"""Characterization tests for GStreamer sink/element discovery.

Freezes the Linux behavior: with the standard GStreamer plugins installed, the
ALSA/PulseAudio/System sinks must be discovered and registered as outputs. This
is the anti-regression reference for the availability-filter work (Phase 3): on
Linux, where every sink is available, nothing must disappear from the UI.
"""

import pytest

# These imports pull in PyQt5 and GStreamer (gi); skip cleanly without them.
pytest.importorskip("gi")
pytest.importorskip("PyQt5")

from lisp.plugins.gst_backend.gi_repository import Gst  # noqa: E402

Gst.init(None)


def _gst_has(element):
    return Gst.ElementFactory.find(element) is not None


@pytest.fixture(scope="module")
def elements():
    from lisp.plugins.gst_backend import elements as _elements

    _elements.load()
    return _elements


def test_autosink_always_registered(elements):
    """The cross-platform default sink must always be available."""
    assert "AutoSink" in elements.outputs()


@pytest.mark.skipif(not _gst_has("alsasink"), reason="alsasink not installed")
def test_alsa_sink_registered_when_available(elements):
    assert "AlsaSink" in elements.outputs()


@pytest.mark.skipif(not _gst_has("pulsesink"), reason="pulsesink not installed")
def test_pulse_sink_registered_when_available(elements):
    assert "PulseSink" in elements.outputs()
