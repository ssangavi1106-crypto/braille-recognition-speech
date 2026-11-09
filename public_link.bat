@echo off
title Braille Studio - Public Link
color 0A
echo ================================================================
echo   BRAILLE STUDIO - Getting your PUBLIC LINK...
echo   (Server should already be running in another window)
echo ================================================================
echo.
echo Starting Cloudflare Tunnel... please wait for the public URL...
echo.
echo >>> Your public link will appear below <<<
echo     It will look like: https://xxxx.trycloudflare.com
echo.
echo Checking Flask at http://127.0.0.1:5000/...
powershell -NoProfile -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/' -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { exit 0 } } catch { exit 1 }; exit 1"
if errorlevel 1 (
    echo ERROR: Flask is not responding on port 5000.
    echo Start the app with run.bat, then run this script again.
    pause
    exit /b 1
)
if not exist "%ProgramFiles(x86)%\cloudflared\cloudflared.exe" (
    echo ERROR: cloudflared was not found. Install Cloudflare Tunnel first.
    pause
    exit /b 1
)
"%ProgramFiles(x86)%\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5000
echo.
pause
