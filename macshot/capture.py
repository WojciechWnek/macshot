"""Interactive screenshot capture - the native ``Cmd+Shift+4`` flow.

MacShot does not implement screen capture itself.  It runs::

    screencapture -i <path>

which is the same macOS service behind ``Cmd+Shift+4``:

* drag to select a region
* press Space to switch to window selection
* press Esc to cancel

The file is written to the system screenshot folder, with the same name
pattern macOS uses for the keyboard shortcut.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

SCREENCAPTURE = "/usr/sbin/screencapture"
DEFAULTS = "/usr/bin/defaults"
OPEN = "/usr/bin/open"

SCREEN_RECORDING_SETTINGS_URL = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
)

#: Formats macOS can save screenshots in and screencapture can write.
CAPTURE_TYPES = frozenset({"png", "jpg", "tiff", "pdf"})

_TCC_MARKERS = (
    "not authorized",
    "screen recording",
    "permission",
    "could not create image",
)
_FAILURE_MARKERS = _TCC_MARKERS + ("cannot write", "failed", "error")


class CaptureError(RuntimeError):
    """The capture failed for a reason other than the user cancelling."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


class CaptureCancelled(Exception):
    """The user pressed Esc or dismissed the native selection UI."""


def _read_default(*keys: str, default: str = "") -> str:
    """Read a key from ``defaults``; return ``default`` on any problem."""
    try:
        proc = subprocess.run(
            [DEFAULTS, "read", *keys],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return default
    if proc.returncode != 0:
        return default
    return proc.stdout.strip() or default


def screenshot_directory() -> Path:
    """The folder macOS is configured to save screenshots into."""
    location = _read_default("com.apple.screencapture", "location")
    if location:
        return Path(location).expanduser()
    return Path.home() / "Desktop"


def screenshot_prefix() -> str:
    """The filename prefix (macOS calls it "name", default "Screenshot")."""
    return _read_default(
        "com.apple.screencapture", "name", default="Screenshot"
    )


def screenshot_extension() -> str:
    """The configured screenshot file type, restricted to safe values."""
    value = _read_default(
        "com.apple.screencapture", "type", default="png"
    ).lower()
    if value == "jpeg":
        value = "jpg"
    return value if value in CAPTURE_TYPES else "png"


def _uses_24_hour_clock() -> bool:
    """Best-effort check of the system time format.

    macOS names screenshots with the user's clock format.  ``en_US`` (this
    machine) uses 12-hour time with AM/PM; an explicit 24-hour override wins.
    """
    forced_24 = _read_default("-g", "AppleICUForce24HourTime").lower()
    if forced_24 in {"1", "true", "yes"}:
        return True
    forced_12 = _read_default("-g", "AppleICUForce12HourTime").lower()
    if forced_12 in {"1", "true", "yes"}:
        return False
    return False


def _timestamp(now: datetime) -> str:
    if _uses_24_hour_clock():
        return now.strftime("%Y-%m-%d at %H.%M.%S")
    return now.strftime("%Y-%m-%d at %I.%M.%S %p")


def unique_path(directory: Path, stem: str, suffix: str) -> Path:
    """Avoid overwriting an existing screenshot."""
    candidate = directory / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = directory / f"{stem} {counter}{suffix}"
        counter += 1
    return candidate


def take_screenshot(now: datetime | None = None) -> Path:
    """Run the interactive ``Cmd+Shift+4`` selection and return the file.

    Raises :class:`CaptureCancelled` if the user presses Esc, and
    :class:`CaptureError` for real failures.
    """
    directory = screenshot_directory()
    directory.mkdir(parents=True, exist_ok=True)

    stem = f"{screenshot_prefix()} {_timestamp(now or datetime.now())}"
    extension = screenshot_extension()
    path = unique_path(directory, stem, f".{extension}")

    command = [SCREENCAPTURE, "-i"]
    if extension != "png":
        command += ["-t", extension]
    command.append(str(path))

    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise CaptureError(
            "Could not find screencapture. Is this macOS?"
        ) from exc

    written = path.exists() and path.stat().st_size > 0
    if written:
        return path

    if path.exists():
        path.unlink(missing_ok=True)

    stderr = (proc.stderr or "").strip()
    lowered = stderr.lower()

    if any(marker in lowered for marker in _TCC_MARKERS):
        raise CaptureError(
            "macOS blocked the screenshot.",
            hint=(
                "Open System Settings -> Privacy & Security -> Screen Recording "
                "and enable the app running MacShot, then try again."
            ),
        )
    if any(marker in lowered for marker in _FAILURE_MARKERS):
        raise CaptureError(
            f"screencapture failed: {stderr or 'unknown error'}"
        )

    raise CaptureCancelled(stderr or "Screenshot cancelled.")


def reveal_in_finder(path: str | Path) -> None:
    """Show the saved screenshot in a Finder window."""
    subprocess.run([OPEN, "-R", str(path)], check=False)


def open_screen_recording_settings() -> None:
    subprocess.run([OPEN, SCREEN_RECORDING_SETTINGS_URL], check=False)
