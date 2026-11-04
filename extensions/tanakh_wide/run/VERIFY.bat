@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul && (py -3.12 project.py verify & exit /b %errorlevel%)
python project.py verify
exit /b %errorlevel%
