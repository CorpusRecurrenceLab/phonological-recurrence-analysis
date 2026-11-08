@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run/tanakh.py prepare
  if errorlevel 1 exit /b 1
  py -3 run/tanakh.py sources
) else (
  python run/tanakh.py prepare
  if errorlevel 1 exit /b 1
  python run/tanakh.py sources
)
exit /b %errorlevel%
