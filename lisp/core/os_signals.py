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

import logging
import signal

logger = logging.getLogger(__name__)

# Signals that should trigger a graceful application quit, in priority order.
# SIGINT exists on every platform; SIGTERM is POSIX and present on most (but
# is not guaranteed); SIGBREAK is the Windows Ctrl+Break equivalent of SIGTERM.
# Using capability detection (hasattr) rather than a `sys.platform` branch keeps
# this the single, extensible decision point for OS signal handling.
_QUIT_SIGNALS = ("SIGINT", "SIGTERM", "SIGBREAK")


def install_quit_handler(handler):
    """Register `handler` for every quit signal available on this platform.

    Signals absent on the current platform (e.g. SIGTERM/SIGBREAK on some
    systems) are skipped instead of raising, so application startup never
    crashes on an unsupported signal.

    :return: the list of signal names actually registered.
    """
    registered = []
    for name in _QUIT_SIGNALS:
        signum = getattr(signal, name, None)
        if signum is None:
            continue
        try:
            signal.signal(signum, handler)
            registered.append(name)
        except (ValueError, OSError, RuntimeError):
            # e.g. not called from the main thread, or unsupported here.
            logger.debug("Could not register signal %s", name, exc_info=True)

    return registered
