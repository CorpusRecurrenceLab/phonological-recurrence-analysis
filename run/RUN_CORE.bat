@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 run/project.py core
) else (
  python run/project.py core
)
exit /b %ERRORLEVEL%
