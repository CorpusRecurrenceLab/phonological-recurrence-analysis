@echo off
setlocal
cd /d "%~dp0.."
python run/project.py nakdan-assemble
exit /b %errorlevel%
