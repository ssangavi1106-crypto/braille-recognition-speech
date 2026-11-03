@echo off
title Braille Studio - Public Online Launcher
echo ========================================================
echo   Starting Braille Studio Server & Generating Public Link
echo ========================================================
echo.
echo [1/2] Starting server...
start /B .\.venv\Scripts\python.exe app.py
timeout /t 2 >nul
echo [2/2] Generating your live public link...
echo.
echo >>> Look for the URL below (e.g. https://xxxx.loca.lt) <<<
echo.
npx localtunnel --port 5000
pause

