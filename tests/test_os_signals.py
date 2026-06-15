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

"""Tests for OS signal registration (Phase 1, P-06).

This module is Qt-free on purpose so it runs on every CI runner, including the
Windows/macOS smoke jobs. ``signal.signal`` is monkeypatched to a recorder so
the tests neither touch the process' real handlers nor require the main thread.
"""

import signal

from lisp.core.os_signals import install_quit_handler


def _patch_signal(monkeypatch):
    """Replace signal.signal with a recorder; return the recorded list."""
    calls = []
    monkeypatch.setattr(signal, "signal", lambda s, h: calls.append(s))
    return calls


def _handler(*_):
    pass


def test_registers_sigint_always(monkeypatch):
    _patch_signal(monkeypatch)
    registered = install_quit_handler(_handler)
    assert "SIGINT" in registered


def test_missing_sigterm_does_not_raise(monkeypatch):
    """Simulate a platform without SIGTERM: registration must not crash."""
    _patch_signal(monkeypatch)
    monkeypatch.delattr(signal, "SIGTERM", raising=False)
    monkeypatch.delattr(signal, "SIGBREAK", raising=False)

    registered = install_quit_handler(_handler)

    assert "SIGTERM" not in registered
    assert "SIGINT" in registered  # SIGINT still wired up


def test_unsupported_signal_is_skipped(monkeypatch):
    """If signal.signal raises for a signal, it is skipped, not propagated."""

    def raising_signal(s, h):
        if s == signal.SIGINT:
            raise ValueError("not supported in this context")

    monkeypatch.setattr(signal, "signal", raising_signal)

    # Must not raise even though SIGINT registration fails.
    registered = install_quit_handler(_handler)
    assert "SIGINT" not in registered
