"""``python -m macshot`` launches the MacShot window."""

from __future__ import annotations


def main() -> int:
    from .gui import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
