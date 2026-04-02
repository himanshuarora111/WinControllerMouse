@echo off
setlocal

:: 1. Check for Admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please right-click and 'Run as Administrator' to uninstall.
    pause
    exit /b
)

echo Stopping CouchCursor if running...
:: Kill the process and all its child processes (/T)
taskkill /F /IM CouchCursor.exe /T >nul 2>&1

echo Removing CouchCursor from Task Scheduler...
schtasks /delete /tn "CouchCursor" /f >nul 2>&1
if %errorLevel% == 0 (
    echo Task removed.
) else (
    echo Task not found ^(already removed^).
)

echo Cleaning up files...
set "INSTALL_DIR=C:\CouchCursor"
if exist "%INSTALL_DIR%" (
    :: Small delay to ensure the exe releases its file lock after being killed
    timeout /t 2 /nobreak >nul
    rd /s /q "%INSTALL_DIR%"
    echo Folder removed.
) else (
    echo Folder not found.
)

echo.
echo SUCCESS: CouchCursor has been completely removed from your system.
pause