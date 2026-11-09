@echo off
title Braille Studio - Public Link Generator
color 0A
echo ================================================================
echo   BRAILLE STUDIO - PUBLIC LINK GENERATOR
echo   Make sure run.bat is ALREADY running in another window!
echo ================================================================
echo.
echo Choose a method to get your public link:
echo.
echo [1] localhost.run  (SSH - most reliable)
echo [2] localtunnel    (npx - easy)
echo [3] serveo.net     (SSH - backup)
echo.
set /p choice="Enter 1, 2, or 3: "

if "%choice%"=="1" goto method1
if "%choice%"=="2" goto method2
if "%choice%"=="3" goto method3
goto method1

:method1
echo.
echo Starting localhost.run tunnel...
echo Look for a link like: https://xxxx.localhost.run
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 nokey@localhost.run
goto end

:method2
echo.
echo Starting localtunnel...
echo Look for a link like: https://xxxx.loca.lt
echo.
npx --yes localtunnel --port 5000
goto end

:method3
echo.
echo Starting serveo.net tunnel...
echo Look for a link like: https://xxxx.serveo.net
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 serveo.net
goto end

:end
echo.
pause
