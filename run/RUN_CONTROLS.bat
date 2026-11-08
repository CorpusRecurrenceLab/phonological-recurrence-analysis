@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 src\analysis\poetic_comparators.py || exit /b %errorlevel%
  py -3 src\analysis\comparator_summary.py || exit /b %errorlevel%
  py -3 src\analysis\validate_controls.py || exit /b %errorlevel%
) else (
  python src\analysis\poetic_comparators.py || exit /b %errorlevel%
  python src\analysis\comparator_summary.py || exit /b %errorlevel%
  python src\analysis\validate_controls.py || exit /b %errorlevel%
)
endlocal
