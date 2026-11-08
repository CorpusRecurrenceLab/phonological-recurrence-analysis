@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 run/project.py verify
) else (
  python run/project.py verify
)
exit /b %ERRORLEVEL%
