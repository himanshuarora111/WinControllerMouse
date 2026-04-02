@echo off
setlocal enabledelayedexpansion

:: 1. Force Admin check
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please right-click and 'Run as Administrator'.
    pause
    exit /b
)

:: 2. Paths
set "SOURCE_DIR=%~dp0"
set "INSTALL_DIR=C:\CouchCursor"
set "EXE_NAME=CouchCursor.exe"

echo Source folder: %SOURCE_DIR%
echo Target folder: %INSTALL_DIR%

:: 3. Create folder
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if !errorLevel! neq 0 (
        echo ERROR: Could not create folder
        pause
        exit /b
    )
)

:: 4. Copy EXE
if exist "%SOURCE_DIR%%EXE_NAME%" (
    copy /y "%SOURCE_DIR%%EXE_NAME%" "%INSTALL_DIR%\%EXE_NAME%"
    if !errorLevel! neq 0 (
        echo ERROR: Copy failed
        pause
        exit /b
    )
) else (
    echo ERROR: %EXE_NAME% not found in source folder
    pause
    exit /b
)

:: 5. Delete old task if exists
schtasks /delete /tn "CouchCursor" /f >nul 2>&1

:: 6. Create scheduled task (with delay + proper execution)
echo Creating startup task...

schtasks /create ^
 /tn "CouchCursor" ^
 /tr "\"%INSTALL_DIR%\%EXE_NAME%\"" ^
 /sc onlogon ^
 /delay 0000:05 ^
 /rl highest ^
 /ru "%USERNAME%" ^
 /it ^
 /f

if %errorLevel% neq 0 (
    echo ERROR: Task creation failed
    pause
    exit /b
)

:: 7. Set Working Directory (Crucial for .exe stability)
powershell -Command "$t = Get-ScheduledTask -TaskName 'CouchCursor'; $t.Actions[0].WorkingDirectory = '%INSTALL_DIR%'; Set-ScheduledTask -InputObject $t" >nul 2>&1

echo.
echo SUCCESS! CouchCursor will run after login.
echo It will start 5 seconds after login.

pause