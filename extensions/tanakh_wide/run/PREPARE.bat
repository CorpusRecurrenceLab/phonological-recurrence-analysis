@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul && (py -3.12 project.py prepare %* & exit /b %errorlevel%)
python project.py prepare %*
exit /b %errorlevel%
