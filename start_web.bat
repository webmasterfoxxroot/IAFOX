@echo off
chcp 65001 >nul
title IAFOX - Web Server
call .venv\Scripts\activate.bat
echo Iniciando servidor web...
echo Acesse: http://localhost:8000
echo.
python -m uvicorn iafox.web.api:app --host 0.0.0.0 --port 8000
