@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 run/reproduce_comparisons.py
) else (
  python run/reproduce_comparisons.py
)
exit /b %ERRORLEVEL%
