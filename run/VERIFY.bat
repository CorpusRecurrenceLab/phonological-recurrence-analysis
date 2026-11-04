@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 project.py verify
) else (
  python project.py verify
)
exit /b %ERRORLEVEL%
