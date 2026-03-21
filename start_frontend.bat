@echo off
echo Starting CivicLens Frontend...
cd /d "%~dp0frontend"

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing npm dependencies...
    npm install
)

REM Start Vite dev server
npm run dev
