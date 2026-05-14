@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

echo Starting Name Fight Web...
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.

start "Name Fight Backend" cmd /k "cd /d "%BACKEND%" && python run_web.py"
start "Name Fight Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo Started. Open http://127.0.0.1:5173 in your browser.
endlocal
