@echo off
setlocal
cd /d "%~dp0.."
python run/verify_unified.py
exit /b %errorlevel%
