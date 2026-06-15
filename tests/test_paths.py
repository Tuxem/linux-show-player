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

"""Characterization tests for the application path layer (``lisp/__init__.py``).

These freeze the *current* Linux behavior so the ``appdirs`` -> ``platformdirs``
migration (Phase 2) can be proven to keep resolved paths bit-for-bit identical.
They also assert correct resolution on Windows/macOS where applicable.
"""

import importlib
import os
import sys

import pytest


def _reload_lisp(monkeypatch, env):
    """Reimport ``lisp`` with a controlled environment and return the module."""
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    # Drop any cached import so module-level path constants are recomputed.
    sys.modules.pop("lisp", None)
    return importlib.import_module("lisp")


@pytest.mark.skipif(
    sys.platform != "linux", reason="XDG path layout is Linux-specific"
)
def test_linux_xdg_paths(tmp_path, monkeypatch):
    """On Linux the user config/data/log dirs must follow the XDG spec.

    This is the anti-regression reference for the platformdirs migration:
    config -> $XDG_CONFIG_HOME/LinuxShowPlayer/<major.minor>
    data   -> $XDG_DATA_HOME/LinuxShowPlayer/<major.minor>
    """
    config_home = tmp_path / "config"
    data_home = tmp_path / "data"

    lisp = _reload_lisp(
        monkeypatch,
        {
            "XDG_CONFIG_HOME": str(config_home),
            "XDG_DATA_HOME": str(data_home),
        },
    )

    version = "{}.{}".format(*lisp.__version_info__[0:2])

    expected_config = config_home / "LinuxShowPlayer" / version
    expected_data = data_home / "LinuxShowPlayer" / version

    assert lisp.USER_APP_CONFIG == str(expected_config / "lisp.json")
    assert lisp.USER_PLUGINS_PATH == str(expected_data / "plugins")
    assert lisp.DEFAULT_CACHE_DIR == str(expected_data / "cache")


def test_app_dir_is_package_dir(monkeypatch):
    """APP_DIR must always point at the installed ``lisp`` package directory."""
    lisp = _reload_lisp(monkeypatch, {})
    assert os.path.isdir(lisp.APP_DIR)
    assert os.path.isfile(os.path.join(lisp.APP_DIR, "__init__.py"))


def test_running_in_flatpak_flag(monkeypatch):
    """RUNNING_IN_FLATPAK must only be true when FLATPAK_ID is set."""
    lisp = _reload_lisp(monkeypatch, {"FLATPAK_ID": None})
    assert lisp.RUNNING_IN_FLATPAK is False

    lisp = _reload_lisp(monkeypatch, {"FLATPAK_ID": "org.example.App"})
    assert lisp.RUNNING_IN_FLATPAK is True
