@echo off
setlocal
cd /d "%~dp0.."
python run/reproduce_all.py
exit /b %errorlevel%
