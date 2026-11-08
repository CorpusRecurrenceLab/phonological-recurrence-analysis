@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run/tanakh.py all
) else (
  python run/tanakh.py all
)
exit /b %errorlevel%
