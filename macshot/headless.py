"""Silent capture entry point used by the global hotkey.

This never opens a window.  It runs the same interactive selection as the GUI,
then posts a Notification Center banner with the saved file name.
"""

from __future__ import annotations

import fcntl
from pathlib import Path

from .capture import CaptureCancelled, CaptureError, notify, take_screenshot

LOCK_PATH = (
    Path.home() / "Library" / "Application Support" / "MacShot" / "hotkey.lock"
)


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
        notify("Screenshot failed", message)
        return 1
    except Exception as exc:  # noqa: BLE001 - reported via notification
        notify("Screenshot failed", str(exc))
        return 1
    finally:
        lock.close()

    notify("Screenshot saved", str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
