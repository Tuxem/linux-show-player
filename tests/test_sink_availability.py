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

"""Tests for the GStreamer element availability filter (Phase 3, P-01/02/03).

The filter must drop an element whose backing feature is unavailable, while
leaving available elements (and elements without an is_available() method)
registered. On Linux, where everything is available, nothing is removed.
"""

import pytest

pytest.importorskip("gi")
pytest.importorskip("PyQt5")

from lisp.backend.media_element import ElementType  # noqa: E402
from lisp.plugins.gst_backend import elements  # noqa: E402


class _AvailableOutput:
    ElementType = ElementType.Output

    @staticmethod
    def is_available():
        return True


class _UnavailableOutput:
    ElementType = ElementType.Output

    @staticmethod
    def is_available():
        return False


class _NoCapabilityOutput:
    # No is_available() -> must always be registered.
    ElementType = ElementType.Output


def test_filter_registers_only_available(monkeypatch):
    fakes = [
        ("_AvailableOutput", _AvailableOutput),
        ("_UnavailableOutput", _UnavailableOutput),
        ("_NoCapabilityOutput", _NoCapabilityOutput),
    ]
    monkeypatch.setattr(elements, "load_classes", lambda *a, **k: fakes)

    elements.load()
    outputs = elements.outputs()

    assert "_AvailableOutput" in outputs
    assert "_NoCapabilityOutput" in outputs
    assert "_UnavailableOutput" not in outputs
