"""Tkinter front end: one control, the native ``Cmd+Shift+4`` capture."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import capture

#: Start the selection immediately on launch, like pressing Cmd+Shift+4.
#: Set to False if you prefer to click the button first.
AUTO_START = True


class MacShotApp:
    """A small window around :func:`capture.take_screenshot`."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.busy = False
        self.last_path: Path | None = None

        root.title("MacShot")
        root.geometry("480x270")
        root.minsize(420, 240)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.bind("<Command-n>", lambda _event: self.take_screenshot())
        root.bind("<Return>", lambda _event: self.take_screenshot())

        self.status_var = tk.StringVar(value="Ready.")
        self._build()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="MacShot",
            font=("TkDefaultFont", 20, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            outer,
            text=(
                "Same as \u2318\u21e74: drag to select an area, "
                "press Space for a window, press Esc to cancel."
            ),
            wraplength=430,
            justify="left",
        ).pack(anchor="w", pady=(6, 16))

        self.capture_button = ttk.Button(
            outer,
            text="Take screenshot  (\u2318\u21e74)",
            command=self.take_screenshot,
        )
        self.capture_button.pack(fill="x")

        self.reveal_button = ttk.Button(
            outer,
            text="Show last screenshot in Finder",
            command=self.reveal_last,
            state="disabled",
        )
        self.reveal_button.pack(fill="x", pady=(8, 0))

        ttk.Label(
            outer,
            textvariable=self.status_var,
            wraplength=430,
            justify="left",
        ).pack(anchor="w", pady=(16, 0))

    # -- capture ---------------------------------------------------------
    def take_screenshot(self) -> None:
        if self.busy:
            return

        self.busy = True
        self.capture_button.state(["disabled"])
        self.status_var.set("Select an area...")
        self.root.withdraw()

        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        try:
            path = capture.take_screenshot()
        except capture.CaptureCancelled:
            self.root.after(0, self._cancelled)
        except capture.CaptureError as exc:
            self.root.after(0, self._failed, exc)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            self.root.after(0, self._failed, exc)
        else:
            self.root.after(0, self._succeeded, path)

    def _restore_window(self) -> None:
        self.busy = False
        self.capture_button.state(["!disabled"])
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(400, lambda: self.root.attributes("-topmost", False))

    def _succeeded(self, path: Path) -> None:
        self._restore_window()
        self.last_path = path
        self.reveal_button.state(["!disabled"])
        self.status_var.set(f"Saved {path.name}\n{path.parent}")

    def _cancelled(self) -> None:
        self._restore_window()
        self.status_var.set("Screenshot cancelled.")

    def _failed(self, exc: Exception) -> None:
        self._restore_window()
        self.status_var.set("Screenshot failed.")

        message = str(exc)
        hint = getattr(exc, "hint", None)
        if hint:
            message = f"{message}\n\n{hint}"
            if messagebox.askyesno(
                "Screen Recording permission",
                message + "\n\nOpen System Settings now?",
                parent=self.root,
            ):
                capture.open_screen_recording_settings()
                return
        messagebox.showerror("MacShot", message, parent=self.root)

    # -- actions ---------------------------------------------------------
    def reveal_last(self) -> None:
        if self.last_path is not None:
            capture.reveal_in_finder(self.last_path)


def main() -> int:
    root = tk.Tk()
    app = MacShotApp(root)
    if AUTO_START:
        root.withdraw()
        root.after(150, app.take_screenshot)
    root.mainloop()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
