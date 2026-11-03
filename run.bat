@echo off
title Braille Studio Server
echo Starting Braille Recognition & Speech Studio...
echo Server running at http://localhost:5000
start http://localhost:5000
.\.venv\Scripts\python.exe app.py
pause
