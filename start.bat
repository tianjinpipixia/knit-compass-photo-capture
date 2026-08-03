@echo off
setlocal
cd /d "%~dp0"
set "PORT=8080"
set "URL=http://127.0.0.1:%PORT%/"

where py >nul 2>nul
if not errorlevel 1 (
  echo Starting Knit Compass at %URL%
  start "" "%URL%"
  py -3 -m http.server %PORT% --bind 127.0.0.1
  exit /b %errorlevel%
)

where python >nul 2>nul
if not errorlevel 1 (
  echo Starting Knit Compass at %URL%
  start "" "%URL%"
  python -m http.server %PORT% --bind 127.0.0.1
  exit /b %errorlevel%
)

echo Python 3 was not found.
echo Install Python 3, then run start.bat again.
exit /b 1
