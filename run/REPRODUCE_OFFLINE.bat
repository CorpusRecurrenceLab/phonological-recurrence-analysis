@echo off
setlocal
cd /d "%~dp0.."
python run/reproduce_offline.py
exit /b %errorlevel%
