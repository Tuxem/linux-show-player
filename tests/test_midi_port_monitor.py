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

"""Tests for MIDI port-monitor selection (Phase 5, P-04).

The factory must pick the ALSA sequencer monitor on Linux (pyalsa present),
keeping that code path unchanged, and fall back to the rtmidi polling monitor
elsewhere. The concrete monitor classes are replaced with sentinels so the
selection logic is tested without touching real ALSA/MIDI hardware.
"""

import pytest

# port_monitor imports lisp.ui.ui_utils (Qt); skip cleanly without it.
pytest.importorskip("PyQt5")

from lisp.plugins.midi import port_monitor  # noqa: E402


@pytest.fixture
def sentinels(monkeypatch):
    monkeypatch.setattr(port_monitor, "_ALSAPortMonitor", lambda: "alsa")
    monkeypatch.setattr(port_monitor, "RtmidiPortMonitor", lambda: "rtmidi")
    monkeypatch.setattr(port_monitor, "PortMonitor", lambda: "noop")


def test_prefers_alsa_when_pyalsa_available(monkeypatch, sentinels):
    monkeypatch.setattr(port_monitor, "alsaseq", object())
    monkeypatch.setattr(port_monitor, "rtmidi", object())
    assert port_monitor.create_port_monitor() == "alsa"


def test_falls_back_to_rtmidi_without_pyalsa(monkeypatch, sentinels):
    monkeypatch.setattr(port_monitor, "alsaseq", False)
    monkeypatch.setattr(port_monitor, "rtmidi", object())
    assert port_monitor.create_port_monitor() == "rtmidi"


def test_noop_monitor_when_nothing_available(monkeypatch, sentinels):
    monkeypatch.setattr(port_monitor, "alsaseq", False)
    monkeypatch.setattr(port_monitor, "rtmidi", None)
    assert port_monitor.create_port_monitor() == "noop"
