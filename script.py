import pygame
import subprocess
import sys
import os
from pynput.mouse import Button, Controller

# --- CONFIGURATION ---
MAX_SPEED = 12 
ACCELERATION = 2 
DEADZONE = 0.15
FPS = 120 

def launch_keyboard():
    subprocess.Popen(['cmd', '/c', 'start', 'tabtip.exe'], shell=True)

def launch_keyboard_default():    
    subprocess.Popen(['osk.exe'], shell=True)

def calculate_move(axis_val):
    if abs(axis_val) < DEADZONE:
        return 0
    return (axis_val ** ACCELERATION) if axis_val > 0 else -(abs(axis_val) ** ACCELERATION)

def main():
    pygame.init()
    pygame.joystick.init()
    mouse = Controller()
    clock = pygame.time.Clock()
    joystick = None
    
    # State variable for Pause/Start
    script_active = True 

    print("CouchCursor Started. Press X + A + D-Pad Up + RT to Toggle.")

    while True:
        if joystick is None:
            if pygame.joystick.get_count() > 0:
                joystick = pygame.joystick.Joystick(0)
                joystick.init()
            else:
                pygame.time.wait(500)
                pygame.event.pump()
                continue

        # 1. Event processing (for keyboard launch)
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEREMOVED:
                joystick = None
            
            # Only allow opening the keyboard if the script is active
            if script_active and event.type == pygame.JOYBUTTONDOWN:
                if joystick.get_button(4): # Require holding LB (Button 4) for safety
                    if event.button == 0:  # A Button
                        launch_keyboard()
                    if event.button == 1:  # B Button
                        launch_keyboard_default()

        if joystick:
            # ---------------------------------------------------------
            # 2. MULTI-BUTTON TOGGLE LOGIC
            # ---------------------------------------------------------
            # A = Button 0 | X = Button 2
            btn_a = joystick.get_button(0)
            btn_x = joystick.get_button(2)
            
            # D-Pad = Hat 0 (Returns a tuple: (x, y). Up is y=1)
            hat_x, hat_y = joystick.get_hat(0)
            dpad_up = (hat_y == 1)
            
            # RT = Axis 5 (Greater than 0.5 means it's pulled)
            rt_pulled = joystick.get_axis(5) > 0.5

            # If all 4 are pressed simultaneously
            if btn_a and btn_x and dpad_up and rt_pulled:
                script_active = not script_active  # Toggle the state
                state_text = "ACTIVE" if script_active else "PAUSED"
                print(f"CouchCursor State: {state_text}")
                
                # Wait half a second so it doesn't flicker on/off 60 times a second
                pygame.time.wait(500) 

            # ---------------------------------------------------------
            # 3. MOVEMENT & CLICK LOGIC (Only runs if script_active)
            # ---------------------------------------------------------
            if script_active:
                # Movement
                ls_h = calculate_move(joystick.get_axis(0))
                ls_v = calculate_move(joystick.get_axis(1))
                rs_h = calculate_move(joystick.get_axis(2))
                rs_v = calculate_move(joystick.get_axis(3))

                final_dx = ls_h + rs_h
                final_dy = ls_v + rs_v

                if final_dx != 0 or final_dy != 0:
                    mouse.move(int(final_dx * MAX_SPEED), int(final_dy * MAX_SPEED))

                # Clicks (RT is 5, LT is 4)
                rt = joystick.get_axis(5)
                lt = joystick.get_axis(4)

                # We add a check so clicking doesn't trigger during the pause combo
                if rt > 0.5 and not (btn_a and btn_x and dpad_up): 
                    mouse.press(Button.left)
                    mouse.release(Button.left)
                    pygame.time.wait(200)
                
                if lt > 0.5: 
                    mouse.press(Button.right)
                    mouse.release(Button.right)
                    pygame.time.wait(200)

        clock.tick(FPS)

# for build do pyinstaller --noconsole --onefile --name CouchCursor script.py
if __name__ == "__main__":
    try:
        main()
    except Exception:
        pygame.quit()