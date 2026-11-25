# AGENTS.md

Guidance for AI agents and humans working on MacShot.

## What this project is

MacShot is a single-purpose macOS app: it reproduces the **⌘⇧4** screenshot
flow. A small Tkinter window launches the native interactive selection via
`/usr/sbin/screencapture -i`, then reports where the file was saved.

There is no custom screen-capture code, no image post-processing, and no
third-party runtime dependency.

## Behavior contract

Do not change these without an explicit request:

1. **Interactive selection only.** Drag a region, Space toggles window mode,
   Esc cancels. This is `screencapture -i`.
2. **Native save location and naming.** Read the system screenshot settings and
   save exactly where the keyboard shortcut would.
3. **Native defaults.** Sound on, cursor excluded, window shadow included.
   That means: do **not** pass `-x`, `-C`, or `-o`.
4. **Window hides during selection**, then reappears with the result. Cancelling
   also returns the window.
5. **Auto-start on launch.** `AUTO_START` in `macshot/gui.py` starts the
   selection immediately. Keep it unless asked to change the launch behavior.

## Golden rules

- Use the native tool for the native job: `screencapture -i` for capture,
  `defaults` for settings, `open` for Finder. Never reimplement capture with a
  library.
- Never build shell command strings. Pass argv lists to `subprocess.run`.
  Never use `shell=True`.
- Do not add capture modes, delay pickers, format pickers, previews, or
  post-processing. The point of this app is to match ⌘⇧4.
- **Do not add tests unless explicitly asked.** The user asked for the test
  suite to be deleted and for no testing at this time.
- Do not add telemetry, network calls, or background services.

## Architecture map

| File | Responsibility |
| --- | --- |
| `macshot/capture.py` | System settings, filename generation, `screencapture -i`, cancel/error mapping, reveal in Finder |
| `macshot/gui.py` | Tkinter window, auto-start, worker thread, result/error UI |
| `macshot/__main__.py` | `python -m macshot` entry point |
| `bin/macshot` | Source-checkout launcher (sets `PYTHONPATH`) |

Flow:

```
launch → GUI withdraws → screencapture -i <path>
       → success: show saved path + "Show in Finder"
       → Esc: show "Screenshot cancelled."
       → error: show message (and Screen Recording hint)
```

## Native contract: `screencapture -i`

- `-i` opens the interactive selection UI: drag for a region, Space for a
  window, Esc to cancel.
- Do not pass `-x` — the keyboard shortcut plays the shutter sound.
- Do not pass `-C` — the keyboard shortcut does not include the cursor.
- Do not pass `-o` — window captures keep their shadow by default.
- A file argument is required; MacShot computes the path first.
- **Exit codes are not reliable.** Verify that the output file exists and has a
  non-zero size.
- Cancelling leaves no file. Remove a zero-byte file if one appears, then raise
  `CaptureCancelled`.
- If stderr mentions permissions/screen recording, raise `CaptureError` with the
  System Settings hint.
- Two interactive captures cannot run simultaneously; the GUI's `busy` flag
  prevents that.

## Save location and naming

Settings are read with `defaults read`:

| Value | Command | Fallback |
| --- | --- | --- |
| Folder | `defaults read com.apple.screencapture location` | `~/Desktop` |
| Prefix | `defaults read com.apple.screencapture name` | `Screenshot` |
| Type | `defaults read com.apple.screencapture type` | `png` |

Naming pattern:

```
<prefix> <YYYY-MM-DD> at <h.mm.ss AM/PM>.<ext>
```

On this Mac (en_US, 12-hour), that produces:

```
Screenshot 2026-11-25 at 12.11.03 PM.png
```

If `AppleICUForce24HourTime` is set, use `HH.MM.SS` with no AM/PM. When a name
already exists, append ` 2`, ` 3`, and so on.

Only allow `png`, `jpg`, `tiff`, and `pdf`; fall back to `png` for any other
configured type.

## Commands

```sh
# Run the app
./bin/macshot
python3 -m macshot

# Install as a command
python3 -m pip install .
macshot
```

## Code conventions

- Python 3.11+, `from __future__ import annotations`, type hints.
- Keep `capture.py` side-effect free until `take_screenshot`; the helpers
  (`screenshot_directory`, `unique_path`, `_timestamp`, …) should stay easy to
  reason about.
- GUI work runs in a worker thread; marshal back to the UI with
  `root.after(0, ...)`.
- Errors: `CaptureCancelled` (Esc), `CaptureError` (real failure, optional
  `hint`).
- Keep user-facing text short and actionable. Mention the exact System
  Settings path when permissions are involved.

## Verifying changes (only when the user asks)

There is no test suite. To check by hand:

1. `./bin/macshot`
2. Drag a region → confirm the file appears in the folder shown in the window
   and opens from Finder.
3. Launch again, press Space, click a window → confirm the window (with shadow)
   is captured.
4. Launch again, press Esc → confirm the window returns and reports
   "Screenshot cancelled."

Do not run captures as part of automated checks unless asked.

## Do not

- Do not add a CLI with extra modes or options.
- Do not add Pillow, mss, ffmpeg, PyObjC, or a custom CoreGraphics pipeline.
- Do not add a preview pane, editor, annotation tools, or upload features.
- Do not add tests while the user has asked for none.
- Do not commit `__pycache__/`, `.venv/`, or screenshots.
