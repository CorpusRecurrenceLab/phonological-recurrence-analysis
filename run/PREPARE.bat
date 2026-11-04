@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 project.py prepare
) else (
  python project.py prepare
)
exit /b %errorlevel%
