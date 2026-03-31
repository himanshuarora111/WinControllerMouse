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
    # Modern Windows 11 keyboard
    subprocess.Popen(['cmd', '/c', 'start', 'tabtip.exe'], shell=True)

def launch_keyboard_default():    
    # Classic On-Screen Keyboard
    subprocess.Popen(['osk.exe'], shell=True)

def calculate_move(axis_val):
    """ Helper to apply deadzone and quadratic acceleration """
    if abs(axis_val) < DEADZONE:
        return 0
    # Maintain direction while applying power curve
    return (axis_val ** ACCELERATION) if axis_val > 0 else -(abs(axis_val) ** ACCELERATION)

def main():
    pygame.init()
    pygame.joystick.init()
    mouse = Controller()
    clock = pygame.time.Clock()
    joystick = None

    print("CouchCursor Active. Using both sticks for movement.")

    while True:
        if joystick is None:
            if pygame.joystick.get_count() > 0:
                joystick = pygame.joystick.Joystick(0)
                joystick.init()
            else:
                pygame.time.wait(500)
                pygame.event.pump()
                continue

        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: # 'A' Button
                    launch_keyboard()
                if event.button == 1: # 'B' Button
                    launch_keyboard_default()
            
            if event.type == pygame.JOYDEVICEREMOVED:
                joystick = None

        if joystick:
            # --- DUAL STICK MOVEMENT ---
            # Left Stick: Axis 0 (H), 1 (V)
            # Right Stick: Axis 2 (H), 3 (V)
            
            ls_h = calculate_move(joystick.get_axis(0))
            ls_v = calculate_move(joystick.get_axis(1))
            rs_h = calculate_move(joystick.get_axis(2))
            rs_v = calculate_move(joystick.get_axis(3))

            # Combine input from both sticks
            final_dx = ls_h + rs_h
            final_dy = ls_v + rs_v

            if final_dx != 0 or final_dy != 0:
                mouse.move(int(final_dx * MAX_SPEED), int(final_dy * MAX_SPEED))

            # --- CLICK LOGIC ---
            # LT: Axis 4 | RT: Axis 5
            lt = joystick.get_axis(4) 
            rt = joystick.get_axis(5)

            if rt > 0.5: # Left Click
                mouse.press(Button.left)
                mouse.release(Button.left)
                pygame.time.wait(200)
            
            if lt > 0.5: # Right Click
                mouse.press(Button.right)
                mouse.release(Button.right)
                pygame.time.wait(200)

        clock.tick(FPS)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pygame.quit()