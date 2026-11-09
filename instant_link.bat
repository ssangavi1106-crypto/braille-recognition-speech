@echo off
title Braille Studio - Direct Public Link
echo ====================================================================
echo   Starting Braille Studio Server & Creating Direct Public Link
echo   (No passwords, no IP verification, opens directly!)
echo ====================================================================
echo.
echo [1/2] Starting Python server...
start /B .\.venv\Scripts\python.exe app.py
timeout /t 2 >nul
echo.
echo [2/2] Generating your direct public link...
echo.
echo >>> Look for the https link generated below (e.g. https://xxxx.lhr.life) <<<
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 nokey@localhost.run
pause
