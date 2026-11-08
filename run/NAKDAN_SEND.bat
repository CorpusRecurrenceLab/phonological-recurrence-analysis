@echo off
setlocal
cd /d "%~dp0.."
python run/project.py nakdan-send
exit /b %errorlevel%
