# PyInstaller entry point for the Windows bundle.
#
# PyInstaller freezes a *script*, not a console_scripts entry point, so this
# thin wrapper just calls the same function as the `linux-show-player` entry
# point declared in pyproject.toml (`lisp.main:main`).

from lisp.main import main

if __name__ == "__main__":
    main()
