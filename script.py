from __future__ import annotations
import ctypes
import os
import subprocess
import sys
import time
import tkinter as tk
from dataclasses import dataclass, field

import pygame
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController


# ---------------------------------------------------------------------------
# Windows sound feedback
# ---------------------------------------------------------------------------

try:
    import winsound
except Exception:
    winsound = None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_NAME = "CouchCursor"

FPS = 120
DEADZONE = 0.15

# Mouse speed tuning
NORMAL_MOUSE_SPEED = 6
SLOW_MOUSE_SPEED = 2
FAST_MOUSE_SPEED = 13
MOUSE_ACCELERATION = 1.3

# Scroll tuning
SCROLL_DEADZONE = 0.20
SCROLL_ACCELERATION = 1.6
SCROLL_NOTCHES_PER_SECOND = 18

# Trigger thresholds
TRIGGER_THRESHOLD = 0.50

# Menu / Start button hold time for pause/resume
MENU_HOLD_SECONDS = 0.75

# Process check interval for Valorant auto-pause
PROCESS_CHECK_INTERVAL_SECONDS = 3.0

# Controller button mapping for a typical Xbox controller in pygame
BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
BUTTON_LB = 4
BUTTON_RB = 5
BUTTON_VIEW = 6       # Back / Select / View
BUTTON_MENU = 7       # Start / Menu

# Axis mapping for a typical Xbox controller in pygame
AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
AXIS_LT = 4
AXIS_RT = 5

# Only block the actual Valorant game by default.
# Do NOT add vgc.exe here unless you want the script to pause almost always,
# because Vanguard can run in the background even when Valorant is not open.
BLOCKED_PROCESS_NAMES = {
    "valorant.exe",
    "valorant-win64-shipping.exe",
}


# ---------------------------------------------------------------------------
# Windows mouse_event movement and scroll
# ---------------------------------------------------------------------------

IS_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x01000
WHEEL_DELTA = 120

if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    # The official signature uses DWORDs, but using c_long for dx/dy/data
    # lets negative relative movement and negative wheel deltas work cleanly.
    user32.mouse_event.argtypes = [
        ctypes.c_ulong,
        ctypes.c_long,
        ctypes.c_long,
        ctypes.c_long,
        ctypes.c_void_p,
    ]
    user32.mouse_event.restype = None
else:
    user32 = None


def win_mouse_move(dx: int, dy: int, fallback_mouse: MouseController | None = None) -> None:
    """
    Send a real relative mouse movement event.

    On Windows this uses user32.mouse_event so Windows sees an actual mouse
    movement event. That helps wake/show the pointer after login.
    """
    dx = int(dx)
    dy = int(dy)

    if dx == 0 and dy == 0:
        return

    if IS_WINDOWS and user32 is not None:
        user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, None)
    elif fallback_mouse is not None:
        fallback_mouse.move(dx, dy)


def win_vertical_scroll(notches: int) -> None:
    """
    Positive notches scroll up. Negative notches scroll down.
    """
    notches = int(notches)
    if notches == 0:
        return

    if IS_WINDOWS and user32 is not None:
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, notches * WHEEL_DELTA, None)


def win_horizontal_scroll(notches: int) -> None:
    """
    Positive notches scroll right. Negative notches scroll left.
    """
    notches = int(notches)
    if notches == 0:
        return

    if IS_WINDOWS and user32 is not None:
        user32.mouse_event(MOUSEEVENTF_HWHEEL, 0, 0, notches * WHEEL_DELTA, None)


def wake_cursor(fallback_mouse: MouseController | None = None) -> None:
    """
    Sends tiny real mouse movement events with zero net movement.

    This is meant to fix the issue where the pointer is invisible after login
    until the physical wireless mouse is moved.
    """
    win_mouse_move(1, 0, fallback_mouse)
    win_mouse_move(-1, 0, fallback_mouse)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def beep_active() -> None:
    if winsound is None:
        return
    try:
        winsound.Beep(900, 110)
    except Exception:
        try:
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass


def beep_paused() -> None:
    if winsound is None:
        return
    try:
        winsound.Beep(420, 140)
    except Exception:
        try:
            winsound.MessageBeep(winsound.MB_ICONHAND)
        except Exception:
            pass


def beep_warning() -> None:
    if winsound is None:
        return
    try:
        winsound.Beep(300, 160)
    except Exception:
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass


def apply_curve(value: float, deadzone: float, acceleration: float) -> float:
    """
    Applies deadzone and acceleration curve.

    Returns a value from -1.0 to 1.0.
    """
    value = float(value)

    if abs(value) <= deadzone:
        return 0.0

    sign = 1.0 if value > 0 else -1.0

    # Rescale so movement starts smoothly after the deadzone.
    normalized = (abs(value) - deadzone) / (1.0 - deadzone)
    normalized = max(0.0, min(1.0, normalized))

    return sign * (normalized ** acceleration)


def safe_axis(joystick: pygame.joystick.Joystick, axis_index: int, default: float = 0.0) -> float:
    try:
        if axis_index < joystick.get_numaxes():
            return float(joystick.get_axis(axis_index))
    except Exception:
        pass
    return default


def safe_button(joystick: pygame.joystick.Joystick, button_index: int) -> bool:
    try:
        if button_index < joystick.get_numbuttons():
            return bool(joystick.get_button(button_index))
    except Exception:
        pass
    return False


def safe_hat(joystick: pygame.joystick.Joystick, hat_index: int = 0) -> tuple[int, int]:
    try:
        if joystick.get_numhats() > hat_index:
            x, y = joystick.get_hat(hat_index)
            return int(x), int(y)
    except Exception:
        pass
    return 0, 0


def trigger_pressed(axis_value: float) -> bool:
    """
    Works for common trigger ranges:
    - Rest -1.0, pressed +1.0
    - Rest  0.0, pressed +1.0
    """
    return axis_value > TRIGGER_THRESHOLD


def launch_touch_keyboard() -> None:
    """
    Opens the Windows touch keyboard, with a fallback to the OSK keyboard.
    """
    if not IS_WINDOWS:
        return

    try:
        # 1. First try TabTip (Windows 10/11 Touch Keyboard)
        subprocess.Popen(['cmd', '/c', 'start', 'tabtip.exe'], shell=True)
        
        # Give Windows a tiny moment to process the command
        time.sleep(0.2)
        
        # 2. Fire the OSK fallback just in case TabTip fails to appear
        # (Windows will usually ignore the second command if TabTip is already taking focus)
        subprocess.Popen(['osk.exe'], shell=True)
        
    except Exception as exc:
        print(f"{APP_NAME}: Failed to launch keyboard: {exc}")


def is_blocked_process_running() -> bool:
    """
    Returns True if Valorant is running.

    This intentionally checks only the actual game processes by default.
    Vanguard services may run in the background, so blocking on vgc.exe would
    make the script pause even when Valorant is not open.
    """
    if not IS_WINDOWS:
        return False

    try:
        output = subprocess.check_output(
            ["tasklist"],
            text=True,
            errors="ignore",
            creationflags=CREATE_NO_WINDOW,
        ).lower()

        return any(process_name in output for process_name in BLOCKED_PROCESS_NAMES)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

class ControlOverlay:
    def __init__(self) -> None:
        self.visible = True
        self.last_text = ""

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.84)

        self.bg = "#111111"
        self.fg = "#f2f2f2"

        self.root.configure(bg=self.bg)

        self.label = tk.Label(
            self.root,
            text=f"{APP_NAME}: Initializing...",
            justify="left",
            anchor="nw",
            bg=self.bg,
            fg=self.fg,
            padx=15,
            pady=10,
            font=("Consolas", 10),
        )
        self.label.pack(expand=True, fill="both")

        self.root.update_idletasks()
        self._position_top_right()
        self._make_click_through()

    def _position_top_right(self) -> None:
        try:
            self.root.update_idletasks()
            screen_width = self.root.winfo_screenwidth()
            window_width = self.root.winfo_reqwidth()

            x = max(0, screen_width - window_width - 20)
            y = 20

            self.root.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _make_click_through(self) -> None:
        """
        Make the overlay ignore mouse clicks on Windows.
        """
        if not IS_WINDOWS:
            return

        try:
            # Using wm_frame() gets the top-level OS window container.
            # Using winfo_id() just gets the client area, which causes the black screen bug.
            hwnd = int(self.root.wm_frame(), 16)

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080

            if ctypes.sizeof(ctypes.c_void_p) == 8:
                get_window_long = user32.GetWindowLongPtrW
                set_window_long = user32.SetWindowLongPtrW
            else:
                get_window_long = user32.GetWindowLongW
                set_window_long = user32.SetWindowLongW

            current_style = get_window_long(hwnd, GWL_EXSTYLE)
            new_style = current_style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
            set_window_long(hwnd, GWL_EXSTYLE, new_style)
        except Exception:
            pass

    def show(self) -> None:
        self.visible = True
        try:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self._position_top_right()
        except Exception:
            pass

    def hide(self) -> None:
        self.visible = False
        try:
            self.root.withdraw()
        except Exception:
            pass

    def toggle(self) -> None:
        if self.visible:
            self.hide()
        else:
            self.show()

    def update(self, text: str) -> None:
        try:
            if text != self.last_text:
                self.label.configure(text=text)
                self.last_text = text
                self._position_top_right()

            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            pass
        except Exception:
            pass

    def close(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass


def create_overlay() -> ControlOverlay | None:
    try:
        return ControlOverlay()
    except Exception as exc:
        print(f"{APP_NAME}: Overlay disabled because tkinter failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

@dataclass
class AppState:
    script_active: bool = True
    valorant_detected: bool = False
    valorant_auto_paused_once: bool = False

    left_mouse_down: bool = False
    right_mouse_down: bool = False

    dpad_keys_down: set = field(default_factory=set)

    menu_down_time: float | None = None
    menu_hold_toggled: bool = False

    scroll_accum_x: float = 0.0
    scroll_accum_y: float = 0.0

    last_process_check_time: float = 0.0


# ---------------------------------------------------------------------------
# Input actions
# ---------------------------------------------------------------------------

def press_mouse_button(
    mouse: MouseController,
    state: AppState,
    button: Button,
) -> None:
    if button == Button.left and not state.left_mouse_down:
        mouse.press(Button.left)
        state.left_mouse_down = True

    elif button == Button.right and not state.right_mouse_down:
        mouse.press(Button.right)
        state.right_mouse_down = True


def release_mouse_button(
    mouse: MouseController,
    state: AppState,
    button: Button,
) -> None:
    if button == Button.left and state.left_mouse_down:
        mouse.release(Button.left)
        state.left_mouse_down = False

    elif button == Button.right and state.right_mouse_down:
        mouse.release(Button.right)
        state.right_mouse_down = False


def tap_key(keyboard: KeyboardController, key) -> None:
    try:
        keyboard.press(key)
        keyboard.release(key)
    except Exception:
        pass


def release_dpad_keys(keyboard: KeyboardController, state: AppState) -> None:
    for key in list(state.dpad_keys_down):
        try:
            keyboard.release(key)
        except Exception:
            pass

    state.dpad_keys_down.clear()


def release_all_inputs(
    mouse: MouseController,
    keyboard: KeyboardController,
    state: AppState,
) -> None:
    release_mouse_button(mouse, state, Button.left)
    release_mouse_button(mouse, state, Button.right)
    release_dpad_keys(keyboard, state)
    state.scroll_accum_x = 0.0
    state.scroll_accum_y = 0.0


def update_dpad_keys(
    joystick: pygame.joystick.Joystick,
    keyboard: KeyboardController,
    state: AppState,
) -> None:
    hat_x, hat_y = safe_hat(joystick)

    desired_keys = set()

    if hat_x < 0:
        desired_keys.add(Key.left)
    elif hat_x > 0:
        desired_keys.add(Key.right)

    if hat_y > 0:
        desired_keys.add(Key.up)
    elif hat_y < 0:
        desired_keys.add(Key.down)

    keys_to_release = state.dpad_keys_down - desired_keys
    keys_to_press = desired_keys - state.dpad_keys_down

    for key in keys_to_release:
        try:
            keyboard.release(key)
        except Exception:
            pass

    for key in keys_to_press:
        try:
            keyboard.press(key)
        except Exception:
            pass

    state.dpad_keys_down = desired_keys


def get_speed_mode(joystick: pygame.joystick.Joystick) -> tuple[str, int]:
    lt = safe_axis(joystick, AXIS_LT)
    rt = safe_axis(joystick, AXIS_RT)

    rt_slow = trigger_pressed(rt)
    lt_fast = trigger_pressed(lt)

    # Slow wins if both are held, because it is safer for precision.
    if rt_slow:
        return "SLOW", SLOW_MOUSE_SPEED

    if lt_fast:
        return "FAST", FAST_MOUSE_SPEED

    return "NORMAL", NORMAL_MOUSE_SPEED


def handle_mouse_movement(
    joystick: pygame.joystick.Joystick,
    mouse: MouseController,
) -> str:
    speed_mode, speed = get_speed_mode(joystick)

    left_x = apply_curve(
        safe_axis(joystick, AXIS_LEFT_X),
        DEADZONE,
        MOUSE_ACCELERATION,
    )
    left_y = apply_curve(
        safe_axis(joystick, AXIS_LEFT_Y),
        DEADZONE,
        MOUSE_ACCELERATION,
    )

    dx = int(left_x * speed)
    dy = int(left_y * speed)

    if dx != 0 or dy != 0:
        win_mouse_move(dx, dy, mouse)

    return speed_mode


def handle_scroll(
    joystick: pygame.joystick.Joystick,
    state: AppState,
    dt_seconds: float,
) -> None:
    right_x = apply_curve(
        safe_axis(joystick, AXIS_RIGHT_X),
        SCROLL_DEADZONE,
        SCROLL_ACCELERATION,
    )
    right_y = apply_curve(
        safe_axis(joystick, AXIS_RIGHT_Y),
        SCROLL_DEADZONE,
        SCROLL_ACCELERATION,
    )

    # Axis right_y is usually positive when stick is moved down.
    # Wheel notches are positive for up, negative for down.
    state.scroll_accum_y += (-right_y) * SCROLL_NOTCHES_PER_SECOND * dt_seconds

    # Horizontal wheel: positive is usually scroll right.
    state.scroll_accum_x += right_x * SCROLL_NOTCHES_PER_SECOND * dt_seconds

    if abs(state.scroll_accum_y) >= 1.0:
        notches_y = int(state.scroll_accum_y)
        win_vertical_scroll(notches_y)
        state.scroll_accum_y -= notches_y

    if abs(state.scroll_accum_x) >= 1.0:
        notches_x = int(state.scroll_accum_x)
        win_horizontal_scroll(notches_x)
        state.scroll_accum_x -= notches_x


def toggle_script_active(
    mouse: MouseController,
    keyboard: KeyboardController,
    state: AppState,
) -> None:
    # Check immediately before resuming so it cannot be re-enabled while
    # Valorant is open.
    currently_blocked = is_blocked_process_running()

    if currently_blocked:
        state.valorant_detected = True
        state.script_active = False
        state.valorant_auto_paused_once = True
        release_all_inputs(mouse, keyboard, state)
        print(f"{APP_NAME}: Auto-paused because Valorant is running.")
        beep_warning()
        return

    state.valorant_detected = False
    state.script_active = not state.script_active

    if state.script_active:
        state.valorant_auto_paused_once = False
        wake_cursor(mouse)
        print(f"{APP_NAME}: ACTIVE")
        beep_active()
    else:
        release_all_inputs(mouse, keyboard, state)
        print(f"{APP_NAME}: PAUSED")
        beep_paused()


def handle_button_event(
    event,
    mouse: MouseController,
    keyboard: KeyboardController,
    state: AppState,
    overlay: ControlOverlay | None,
) -> None:
    now = time.monotonic()
    is_down = event.type == pygame.JOYBUTTONDOWN
    is_up = event.type == pygame.JOYBUTTONUP
    button = event.button

    # View / Back toggles overlay even when paused.
    if is_down and button == BUTTON_VIEW:
        if overlay is not None:
            overlay.toggle()
        return

    # Menu / Start:
    # tap = Enter
    # hold = pause/resume
    if button == BUTTON_MENU:
        if is_down:
            state.menu_down_time = now
            state.menu_hold_toggled = False
            return

        if is_up:
            if state.menu_down_time is not None and not state.menu_hold_toggled:
                if state.script_active and not state.valorant_detected:
                    tap_key(keyboard, Key.enter)

            state.menu_down_time = None
            state.menu_hold_toggled = False
            return

    # Other controls only work while active and not blocked.
    if not state.script_active or state.valorant_detected:
        return

    if button == BUTTON_A:
        if is_down:
            press_mouse_button(mouse, state, Button.left)
        elif is_up:
            release_mouse_button(mouse, state, Button.left)
        return

    if button == BUTTON_B:
        if is_down:
            press_mouse_button(mouse, state, Button.right)
        elif is_up:
            release_mouse_button(mouse, state, Button.right)
        return

    if is_down and button == BUTTON_Y:
        launch_touch_keyboard()
        return

    if is_down and button == BUTTON_RB:
        tap_key(keyboard, Key.esc)
        return


def handle_menu_hold(
    mouse: MouseController,
    keyboard: KeyboardController,
    state: AppState,
) -> None:
    if state.menu_down_time is None:
        return

    if state.menu_hold_toggled:
        return

    now = time.monotonic()
    held_for = now - state.menu_down_time

    if held_for >= MENU_HOLD_SECONDS:
        toggle_script_active(mouse, keyboard, state)
        state.menu_hold_toggled = True


def check_valorant_auto_pause(
    mouse: MouseController,
    keyboard: KeyboardController,
    state: AppState,
) -> None:
    now = time.monotonic()

    if now - state.last_process_check_time < PROCESS_CHECK_INTERVAL_SECONDS:
        return

    state.last_process_check_time = now

    detected = is_blocked_process_running()

    if detected:
        if not state.valorant_detected:
            print(f"{APP_NAME}: Valorant detected. Auto-pausing.")
            beep_warning()

        state.valorant_detected = True
        state.valorant_auto_paused_once = True
        state.script_active = False
        release_all_inputs(mouse, keyboard, state)
        return

    # Valorant is no longer running.
    # Stay paused until the user manually holds Menu / Start to resume.
    if state.valorant_detected:
        print(f"{APP_NAME}: Valorant closed. Hold Menu / Start to resume manually.")

    state.valorant_detected = False


# ---------------------------------------------------------------------------
# Overlay text
# ---------------------------------------------------------------------------

def build_overlay_text(
    joystick: pygame.joystick.Joystick | None,
    state: AppState,
    speed_mode: str,
) -> str:
    if joystick is None:
        return (
            f"{APP_NAME}: WAITING\n"
            "\n"
            "Connect controller\n"
            "View     Hide/show help"
        )

    try:
        controller_name = joystick.get_name()
    except Exception:
        controller_name = "Controller"

    if state.valorant_detected:
        status = "AUTO-PAUSED"
        status_detail = "Valorant detected"
    elif state.script_active:
        status = "ON"
        status_detail = f"Speed: {speed_mode}"
    else:
        status = "PAUSED"
        if state.valorant_auto_paused_once:
            status_detail = "Hold Menu to resume"
        else:
            status_detail = "Hold Menu to resume"

    return (
        f"{APP_NAME}: {status}\n"
        f"{status_detail}\n"
        "\n"
        "LS       Move mouse\n"
        "RS       Scroll\n"
        "A        Left click / drag\n"
        "B        Right click\n"
        "RT       Slow mode\n"
        "LT       Fast mode\n"
        "Y        Touch keyboard\n"
        "RB       Escape\n"
        "D-pad    Arrow keys\n"
        "Menu     Enter\n"
        "Hold Menu Pause/resume\n"
        "View     Hide/show help\n"
        "\n"
        f"{controller_name}"
    )


# ---------------------------------------------------------------------------
# Joystick setup
# ---------------------------------------------------------------------------

def get_first_joystick() -> pygame.joystick.Joystick | None:
    try:
        if pygame.joystick.get_count() <= 0:
            return None

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        return joystick
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    pygame.joystick.init()

    mouse = MouseController()
    keyboard = KeyboardController()
    clock = pygame.time.Clock()
    overlay = create_overlay()
    state = AppState()

    joystick = get_first_joystick()

    print(f"{APP_NAME} started.")
    print("Controls:")
    print("  Left stick  = move mouse")
    print("  Right stick = scroll")
    print("  A           = left click / drag")
    print("  B           = right click")
    print("  RT          = slow mode")
    print("  LT          = fast mode")
    print("  Y           = touch keyboard")
    print("  RB          = Escape")
    print("  D-pad       = arrow keys")
    print("  Menu tap    = Enter")
    print("  Menu hold   = pause/resume")
    print("  View        = hide/show overlay")

    wake_cursor(mouse)

    if joystick is not None:
        print(f"{APP_NAME}: Controller connected: {joystick.get_name()}")
        wake_cursor(mouse)
    else:
        print(f"{APP_NAME}: Waiting for controller...")

    speed_mode = "NORMAL"

    try:
        while True:
            dt_ms = clock.tick(FPS)
            dt_seconds = max(0.001, dt_ms / 1000.0)

            # Process pygame events.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

                if event.type == pygame.JOYDEVICEREMOVED:
                    print(f"{APP_NAME}: Controller disconnected.")
                    release_all_inputs(mouse, keyboard, state)
                    joystick = None
                    continue

                if event.type == pygame.JOYDEVICEADDED:
                    if joystick is None:
                        joystick = get_first_joystick()
                        if joystick is not None:
                            print(f"{APP_NAME}: Controller connected: {joystick.get_name()}")
                            wake_cursor(mouse)
                    continue

                if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                    handle_button_event(event, mouse, keyboard, state, overlay)

            # Reconnect fallback in case JOYDEVICEADDED does not fire.
            if joystick is None:
                joystick = get_first_joystick()
                if joystick is not None:
                    print(f"{APP_NAME}: Controller connected: {joystick.get_name()}")
                    wake_cursor(mouse)

            handle_menu_hold(mouse, keyboard, state)
            check_valorant_auto_pause(mouse, keyboard, state)

            if joystick is not None and state.script_active and not state.valorant_detected:
                speed_mode = handle_mouse_movement(joystick, mouse)
                handle_scroll(joystick, state, dt_seconds)
                update_dpad_keys(joystick, keyboard, state)
            else:
                release_all_inputs(mouse, keyboard, state)
                speed_mode = "NORMAL"

            if overlay is not None:
                overlay.update(build_overlay_text(joystick, state, speed_mode))

    finally:
        release_all_inputs(mouse, keyboard, state)

        if overlay is not None:
            overlay.close()

        pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
    except Exception as exc:
        pygame.quit()
        print(f"{APP_NAME} crashed: {exc}")
        sys.exit(1)
