# MacShot

A tiny macOS app that does the same thing as pressing **⌘⇧4**:

- the window disappears and the native selection crosshair appears
- drag to select a region
- press **Space** to switch to window selection
- press **Esc** to cancel
- the screenshot is saved to the system screenshot folder with the system
  filename pattern

There is no custom capture code. MacShot runs the same native service as the
keyboard shortcut: `screencapture -i`.

## Requirements

- macOS
- Python 3.11+ with Tkinter

## Run

```sh
./bin/macshot
```

or:

```sh
python3 -m macshot
```

Install it as a command:

```sh
python3 -m pip install .
macshot
```

On launch, MacShot immediately starts the selection (like pressing ⌘⇧4). After
the capture, a small window appears with the saved file name and a **Show last
screenshot in Finder** button. Press **Take screenshot** to capture again. If
you cancel, the window returns instead.

To make the app wait for a button click instead of starting immediately, set
`AUTO_START = False` in `macshot/gui.py`.

## Where files are saved

MacShot follows the same system settings as the keyboard shortcut:

| Setting | Read from | Default |
| --- | --- | --- |
| Folder | `com.apple.screencapture location` | `~/Desktop` |
| Name prefix | `com.apple.screencapture name` | `Screenshot` |
| File type | `com.apple.screencapture type` | `png` |

Example filename on this Mac:

```
Screenshot 2026-11-25 at 12.11.03 PM.png
```

If a file with that name already exists, a counter is added (`… 2.png`).

## Capture behavior

MacShot deliberately uses the native defaults, so it matches ⌘⇧4:

- shutter sound is **on** (`-x` is not passed)
- the mouse cursor is **not** included (`-C` is not passed)
- window captures include the **shadow** (`-o` is not passed)
- no delay, no format picker, no extra modes

The only difference from the keyboard shortcut is that macOS's floating
thumbnail is a system UI feature and is not reproduced; MacShot shows the
saved file in its own window instead.

## Global hotkey: Control+Shift+4

Install it once:

```sh
./bin/install-hotkey
```

This compiles a tiny native listener (`tools/MacShotHotkey.swift`) with the
system Swift compiler and installs a LaunchAgent:

```
~/Library/LaunchAgents/com.macshot.hotkey.plist
~/Library/Application Support/MacShot/bin/MacShotHotkey
```

Pressing **Control+Shift+4** from any app launches MacShot. Its window hides
while the native selection UI is open, then returns with the saved file. This
is the default (`--gui`) mode.

If you prefer the silent shortcut — no window, just the native selection and a
Notification Center banner:

```sh
./bin/install-hotkey --silent
```

The listener uses Carbon's `RegisterEventHotKey`, so it does **not** need
Accessibility permission. Logs go to `/tmp/macshot-hotkey.log`.

Remove it with:

```sh
./bin/uninstall-hotkey
```

### If Control+Shift+4 does nothing

1. `install-hotkey` already registers the shortcut. Remove any manual
   assignment you added in **System Settings → Keyboard → Keyboard Shortcuts**
   or in the **Shortcuts** app; two bindings can conflict.
2. Press the shortcut, then check the log:

   ```sh
   tail -f /tmp/macshot-hotkey.log
   ```

   A successful press appends `MacShotHotkey: hotkey pressed`.

3. If no line appears, reinstall the listener:

   ```sh
   ./bin/install-hotkey
   ```

   or choose a different key (below).

### Changing the keys

Edit the two constants at the top of `tools/MacShotHotkey.swift`:

```swift
private let hotKeyModifiers = UInt32(controlKey | shiftKey)
private let hotKeyKeyCode = UInt32(kVK_ANSI_4)
```

Useful Carbon modifier constants: `controlKey`, `shiftKey`, `optionKey`,
`cmdKey`. Key codes: `kVK_ANSI_A` … `kVK_ANSI_Z`, `kVK_ANSI_0` … `kVK_ANSI_9`,
`kVK_Space`, `kVK_Return`, `kVK_Escape`, `kVK_F1` … `kVK_F20`.

Then reinstall:

```sh
./bin/install-hotkey
```

## Permissions

Interactive capture normally works through the system screenshot service. If
macOS blocks it, enable **System Settings → Privacy & Security → Screen
Recording** for the app that launches MacShot (usually Terminal or iTerm).
MacShot detects the common permission error and offers to open the settings
pane.

## How it works

```
macshot/gui.py      small Tkinter window, hides during selection
        │
        ▼
macshot/capture.py  reads system screenshot settings, builds the file name
        │
        ▼
/usr/sbin/screencapture -i <file>
```

The file is written directly to its final path. There is no temp file and no
image post-processing.

## Project layout

```
macshot/
├── __main__.py   # python -m macshot
├── capture.py    # native capture, save location, naming
├── gui.py        # Tkinter launcher window
└── headless.py   # silent capture used by the global hotkey
tools/
└── MacShotHotkey.swift   # Carbon global hotkey listener
bin/
├── macshot               # run the GUI without installing
├── macshot-capture       # silent capture for the hotkey
├── install-hotkey        # compile + install the LaunchAgent
└── uninstall-hotkey      # remove the listener
```

## Tests

Per request, the automated test suite was removed and there is currently no
testing setup.

## License

MIT. See `LICENSE`.
