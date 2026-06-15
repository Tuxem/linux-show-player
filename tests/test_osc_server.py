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

"""Tests for OSC graceful degradation without liblo (Phase 6, P-09).

When the optional native liblo (pyliblo3) dependency is missing, the OSC server
must become a no-op rather than crash, so the plugin keeps loading.
"""

import pytest

# osc_server imports lisp.ui.ui_utils (Qt); skip cleanly without it.
pytest.importorskip("PyQt5")

from lisp.plugins.osc import osc_server  # noqa: E402


def test_server_is_noop_without_liblo(monkeypatch):
    monkeypatch.setattr(osc_server, "ServerThread", None)

    srv = osc_server.OscServer("localhost", 9000, 9001)

    # None of these must raise when liblo is unavailable.
    srv.start()
    assert not srv.is_running()
    srv.send("/some/path", 1, 2, 3)
    srv.stop()
