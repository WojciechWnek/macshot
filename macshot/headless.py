"""Silent capture entry point used by the global hotkey.

This never opens a window, never posts a notification, and never touches the
Dock.  It runs the same interactive selection as the GUI and exits.  Problems
are written to stderr, which the LaunchAgent redirects to
``/tmp/macshot-hotkey.log``.
"""

from __future__ import annotations

import fcntl
import sys
from pathlib import Path

from .capture import CaptureCancelled, CaptureError, take_screenshot

LOCK_PATH = (
    Path.home() / "Library" / "Application Support" / "MacShot" / "hotkey.lock"
)


def _log(message: str) -> None:
    print(f"MacShot: {message}", file=sys.stderr, flush=True)


def _acquire_lock():
    """Return an open, locked file handle, or ``None`` if one is already held.

    Prevents a second hotkey press from starting another selection while the
    first one is still open.
    """
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    handle = open(LOCK_PATH, "w", encoding="utf-8")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def main() -> int:
    lock = _acquire_lock()
    if lock is None:
        return 0

    try:
        path = take_screenshot()
    except CaptureCancelled:
        return 0
    except CaptureError as exc:
        message = str(exc)
        if exc.hint:
            message = f"{message} {exc.hint}"
        _log(message)
        return 1
    except Exception as exc:  # noqa: BLE001 - only logged, never shown
        _log(str(exc))
        return 1
    finally:
        lock.close()

    _log(f"saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
