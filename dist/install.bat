@echo off
:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please right-click and 'Run as Administrator'.
    pause
    exit /b
)

:: Set the installation directory
set "INSTALL_DIR=C:\CouchCursor"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy the EXE from the CURRENT folder to the install directory
copy /y "CouchCursor.exe" "%INSTALL_DIR%\CouchCursor.exe"

echo Registering CouchCursor with Task Scheduler...

:: Create the task to run at logon with Highest Privileges
schtasks /create /tn "CouchCursor" /tr "'%INSTALL_DIR%\CouchCursor.exe'" /sc onlogon /rl highest /f

echo.
echo SUCCESS! CouchCursor is installed and will start at the login screen.
pause