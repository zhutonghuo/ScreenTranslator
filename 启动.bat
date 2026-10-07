@echo off
if not exist "%LOCALAPPDATA%\ScreenTranslator" md "%LOCALAPPDATA%\ScreenTranslator"
echo [%date% %time%] bat launched >> "%LOCALAPPDATA%\ScreenTranslator\launch.log"
if exist "C:\Users\LiuYuming\.workbuddy\binaries\python\envs\default\Scripts\pythonw.exe" goto USEVENV
goto USESYS
:USEVENV
start "ScreenTranslator" "C:\Users\LiuYuming\.workbuddy\binaries\python\envs\default\Scripts\pythonw.exe" "%~dp0main.py"
goto END
:USESYS
where pythonw >nul 2>nul
if errorlevel 1 goto NOPY
start "ScreenTranslator" pythonw "%~dp0main.py"
goto END
:NOPY
echo Python not found, press any key to exit.
pause >nul
:END
