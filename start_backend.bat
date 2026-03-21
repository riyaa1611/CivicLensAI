@echo off
echo Starting CivicLens Backend...
cd /d "%~dp0backend"

REM Install ScaleDown from parent dir (treat as library)
pip install -e .. --quiet

REM Install backend dependencies
pip install -r requirements.txt --quiet

REM Start FastAPI server
python -m uvicorn civiclens.api.server:app --host 0.0.0.0 --port 8000 --reload
