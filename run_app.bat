@echo off
title Hugo AI Launcher
echo ==================================================
echo        HUGO AI - Startup Script
echo ==================================================
echo.

echo [1/2] Starting Backend Server (FastAPI)...
start "Hugo Backend" cmd /k "cd backend && call venv\Scripts\activate && uvicorn app.main:app --reload"

echo [2/2] Starting Frontend App (React)...
start "Hugo Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==================================================
echo  Success! Terminals launched.
echo  frontend: http://localhost:5173
echo  backend:  http://localhost:8000/docs
echo ==================================================
pause
