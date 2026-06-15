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

"""Shared pytest fixtures and headless setup.

These tests are designed to run on the three target platforms without real
audio/MIDI hardware. Heavy optional dependencies (Qt, GStreamer) are imported
lazily inside the tests that need them, via ``pytest.importorskip``, so the
suite degrades gracefully when a dependency is missing.
"""

import os

# Make sure any accidental Qt instantiation never tries to reach a real
# display, on every platform (xvfb on Linux CI, offscreen elsewhere).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
