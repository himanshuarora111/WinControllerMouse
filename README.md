# WinControllerMouse / CouchCursor

Use an Xbox-style controller as a couch-friendly mouse and basic Windows navigation controller.

This project is meant for controlling Windows **after login** from a controller: moving the mouse, clicking, scrolling, opening the touch keyboard, pressing Escape/Enter, and navigating with the D-pad.

The current version is designed around a simple, easy-to-remember layout:

- Left stick moves the mouse
- Right stick scrolls
- `A` left-clicks
- `B` right-clicks
- `RT` slows the cursor for precision
- `LT` speeds up cursor movement
- A small overlay shows the controls in the top-right corner

---

## Important Limitations

### Does Not Work on the Windows Login Screen

This script is a normal user-mode Python program. It starts after a Windows user session is active, so it cannot control the Windows login screen.

It also should not be expected to work on secure Windows desktops such as:

- Windows login screen
- UAC prompts
- Ctrl+Alt+Delete screen
- Some elevated or secure system prompts

For login-screen control, use a real physical keyboard/mouse, a controller that exposes itself as a real HID mouse/keyboard, or another hardware-level solution.

This project does **not** attempt to bypass Windows secure desktop restrictions.

---

### Not Intended for Valorant or Anti-Cheat Games

This tool is for Windows desktop navigation.

It is **not intended to be used in Valorant** or other anti-cheat-protected games. The script includes an auto-pause safety feature that detects Valorant game processes and pauses itself.

By default, the script checks for:

```text
valorant.exe
valorant-win64-shipping.exe
```

It intentionally does **not** block on:

```text
vgc.exe
```

because Vanguard can run in the background even when Valorant is not open. Blocking `vgc.exe` would make the script stay paused almost all the time on systems with Vanguard installed.

---

## Features

- Controller-based mouse movement
- Win32 mouse movement events for better Windows pointer behavior
- Cursor wake fix after login
- Vertical and horizontal scrolling with the right stick
- Left click / drag with `A`
- Right click with `B`
- Precision mode with `RT`
- Fast movement mode with `LT`
- Touch keyboard shortcut with `Y`
- Escape with `RB`
- Enter with `Menu / Start`
- Arrow-key navigation with the D-pad
- Top-right always-on-top control overlay
- Overlay show/hide toggle
- Manual pause/resume
- Valorant auto-pause safety behavior

---

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer recommended
- Xbox-style controller or compatible gamepad
- Required Python packages:
  - `pygame`
  - `pynput`

The script also uses the following Python modules:

- `tkinter`
- `ctypes`
- `subprocess`
- `winsound`

These are included with normal Windows Python installations.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/himanshuarora111/WinControllerMouse.git
cd WinControllerMouse
```

Install dependencies:

```bash
pip install pygame pynput
```

Run the script:

```bash
python script.py
```

---

## Controls

| Controller Input | Action |
|---|---|
| Left stick | Move mouse |
| Right stick up/down | Vertical scroll |
| Right stick left/right | Horizontal scroll |
| `A` | Left click |
| Hold `A` | Hold left mouse button / drag |
| `B` | Right click |
| Hold `B` | Hold right mouse button |
| `RT` | Slow / precision mode |
| `LT` | Fast movement mode |
| `Y` | Open Windows touch keyboard |
| `RB` | Escape |
| D-pad | Arrow keys |
| Tap `Menu / Start` | Enter |
| Hold `Menu / Start` | Pause/resume script |
| `View / Back / Select` | Show/hide overlay |

---

## Speed Modes

The mouse has three movement speeds.

| Mode | How to Activate | Purpose |
|---|---|---|
| Normal | No trigger held | Everyday mouse movement |
| Slow | Hold `RT` | Precise clicking and small UI targets |
| Fast | Hold `LT` | Quickly crossing the screen |

Slow mode is on `RT` because it is easier to hold the right trigger while moving the left stick with your left thumb.

Fast mode is on `LT` because it is used less often.

---

## Overlay

The script shows a small control overlay in the top-right corner of the screen.

It displays:

- Current script status
- Current speed mode
- Main controller controls
- Connected controller name

Press:

```text
View / Back / Select
```

to hide or show the overlay.

The overlay is designed to be small and always on top. On Windows, the script attempts to make it click-through so it does not block mouse clicks.

---

## Pause and Resume

Tap:

```text
Menu / Start
```

to send `Enter`.

Hold:

```text
Menu / Start
```

to pause or resume the script.

When paused, the script releases any held mouse buttons and D-pad keys.

The script also plays a sound when toggling.

| State | Sound |
|---|---|
| Active | Higher beep |
| Paused | Lower beep |
| Valorant detected | Warning beep |

---

## Valorant Auto-Pause Behavior

When Valorant is detected, the script automatically pauses.

While Valorant is running:

- Mouse movement from the controller is disabled
- Clicking from the controller is disabled
- Scrolling from the controller is disabled
- D-pad keyboard input is released
- The overlay shows an auto-paused status

When Valorant closes, the script does **not** automatically resume.

You must hold:

```text
Menu / Start
```

to manually resume.

This is intentional. It avoids accidentally re-enabling controller-to-mouse input while switching in and out of games.

---

## Cursor Visibility Fix

Some wireless mice hide the Windows pointer after login until the physical mouse is moved.

This script sends a tiny real Windows mouse movement when it starts:

```text
+1 pixel, then -1 pixel
```

The net mouse position does not change, but Windows receives a real mouse movement event. This helps make the pointer visible without needing to physically move the wireless mouse.

The script also sends this wake movement when:

- The script starts
- A controller connects
- The script is resumed

---

## Touch Keyboard

Press:

```text
Y
```

to open the Windows touch keyboard.

The script attempts to launch:

```text
TabTip.exe
```

which is the Windows touch keyboard executable.

On some Windows installations, the touch keyboard may behave differently depending on system settings, tablet mode settings, or whether the touch keyboard service is available.

---

## Troubleshooting

### Controller Is Not Detected

Make sure the controller is connected before or after starting the script.

The script attempts to reconnect automatically if a controller is plugged in after launch.

Also check that Windows can see the controller:

```text
Control Panel → Devices and Printers
```

or:

```text
Windows Settings → Bluetooth & devices
```

---

### Buttons Do Not Match the README

Different controllers can report different button indexes through `pygame`.

This script uses a typical Xbox controller mapping.

| Button | pygame Index |
|---|---|
| A | 0 |
| B | 1 |
| X | 2 |
| Y | 3 |
| LB | 4 |
| RB | 5 |
| View / Back | 6 |
| Menu / Start | 7 |

If your controller has different mappings, update these constants near the top of `script.py`:

```python
BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
BUTTON_LB = 4
BUTTON_RB = 5
BUTTON_VIEW = 6
BUTTON_MENU = 7
```

---

### Sticks or Triggers Are Wrong

The script uses a typical Xbox axis mapping.

| Control | pygame Axis |
|---|---|
| Left stick X | 0 |
| Left stick Y | 1 |
| Right stick X | 2 |
| Right stick Y | 3 |
| LT | 4 |
| RT | 5 |

If your controller reports axes differently, update these constants in `script.py`:

```python
AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
AXIS_LT = 4
AXIS_RT = 5
```

---

### Pointer Still Does Not Appear After Login

Try disabling this Windows setting:

```text
Control Panel → Mouse → Pointer Options → Hide pointer while typing
```

Also try disabling USB selective suspend:

```text
Control Panel
→ Power Options
→ Change plan settings
→ Change advanced power settings
→ USB settings
→ USB selective suspend setting
→ Disabled
```

---

### Overlay Does Not Appear

The overlay uses `tkinter`.

Make sure your Python installation includes tkinter. Most official Windows Python installers include it by default.

You can test tkinter with:

```bash
python -m tkinter
```

If a small test window appears, tkinter is working.

---

### Script Works on Desktop but Not in Some Apps

Some elevated apps, secure screens, games, or anti-cheat-protected applications may block or ignore synthetic input.

This script is intended for normal Windows desktop use after login.

---

## Optional: Start Automatically After Login

This script can be started automatically after Windows login using Task Scheduler.

Recommended setup:

1. Open Task Scheduler
2. Create a new task
3. Trigger: `At log on`
4. Action: start Python with this script
5. Run only when the user is logged on

Example action:

```text
Program/script:
python

Add arguments:
"C:\path\to\WinControllerMouse\script.py"
```

This starts the script after login.

It will not make the script work on the Windows login screen.

---

## Project Status

This is a personal Windows couch-control utility.

Current focus:

- Simple controller mouse control
- Comfortable couch navigation
- Easy-to-remember layout
- Safe behavior around Valorant
- Practical Windows pointer wake behavior

Not planned:

- Login-screen control through software
- UAC secure desktop control
- Anti-cheat bypasses
- Low-level input drivers
- Valorant support

---

## License

See `LICENSE`.
