@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run/project.py prepare
) else (
  python run/project.py prepare
)
exit /b %errorlevel%
