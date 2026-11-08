@echo off
setlocal
cd /d "%~dp0.."
python run/project.py nakdan-prepare
exit /b %errorlevel%
