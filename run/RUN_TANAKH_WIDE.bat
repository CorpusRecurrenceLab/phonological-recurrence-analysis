@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 extensions\tanakh_wide\project.py all
) else (
  python extensions\tanakh_wide\project.py all
)
exit /b %errorlevel%
