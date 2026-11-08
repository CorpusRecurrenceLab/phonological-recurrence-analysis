@echo off
setlocal
cd /d "%~dp0.."
python run/project.py download
exit /b %errorlevel%
