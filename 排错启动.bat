@echo off
chcp 65001 >nul
"C:\Users\LiuYuming\.workbuddy\binaries\python\envs\default\Scripts\python.exe" "%~dp0main.py"
echo.
echo -------- program exited, code %errorlevel% --------
pause
