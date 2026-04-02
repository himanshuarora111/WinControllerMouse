# CouchCursor 🎮🖱️

A lightweight, high-performance background utility that turns your XInput gamepad (Xbox controller) into a fully functional Windows mouse. Built specifically for couch-gaming PCs and HTPCs, it allows you to navigate the desktop, click through UAC prompts, and type using the On-Screen Keyboard without ever needing a physical mouse or keyboard.

## ✨ Features
- **Smooth Dual-Stick Navigation:** Combines both thumbsticks with custom deadzones and quadratic acceleration curves for precise desktop control.
- **System-Level Interaction:** Runs with Highest Privileges via Task Scheduler, allowing it to interact with strict Windows UI elements like the On-Screen Keyboard, Task Manager, and Run as Administrator UAC prompts.
- **100% Anti-Cheat Safe:** Operates purely in User-Mode. It does not install kernel-level virtual HID drivers (like reWASD), meaning it is completely safe to leave running alongside strict anti-cheats like Riot Vanguard (Valorant), Ricochet (Call of Duty), or Easy Anti-Cheat.
- **Quick-Toggle Game Mode:** Features a hardcoded multi-button Safety Pin combo to instantly pause the script, ensuring zero input conflict when you launch a game.

## 🚀 Installation
1. Download or clone this repository to your PC.
2. Right-click `install.bat` and select **Run as Administrator**.
3. The script will automatically copy the necessary files to `C:\CouchCursor` and register a background task.
4. Log out and log back in (or restart your PC). CouchCursor will automatically start 5 seconds after you reach the desktop.

## 🎮 Controls
### Mouse Movement & Clicks
- **Left / Right Thumbsticks:** Move Mouse (Use both simultaneously for faster movement)
- **Right Trigger (RT):** Left Click
- **Left Trigger (LT):** Right Click

### On-Screen Keyboard
To prevent accidental pop-ups in menus, you must hold the Left Bumper while pressing the face buttons to summon the keyboard:
- **LB + A:** Open Modern Windows Touch Keyboard
- **LB + B:** Open Classic Windows On-Screen Keyboard (OSK)

## 🛑 Pause / Resume (Game Mode)
When you are ready to play a game, press the following four buttons simultaneously to pause CouchCursor and return your gamepad to normal:
- **X + A + D-Pad Up + Right Trigger**

## 🗑️ Uninstallation
If you need to remove the utility, it leaves no messy registry keys or leftover drivers behind:
1. Navigate to the folder where you originally downloaded the project.
2. Right-click `uninstall.bat` and select **Run as Administrator**.
3. The script will kill the background process, remove the Task Scheduler entry, and delete the `C:\CouchCursor` directory.
