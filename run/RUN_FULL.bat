@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 reproduce_article.py
) else (
  python reproduce_article.py
)
exit /b %ERRORLEVEL%
