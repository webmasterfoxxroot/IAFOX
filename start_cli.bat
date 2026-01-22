@echo off
chcp 65001 >nul
title IAFOX - CLI
call .venv\Scripts\activate.bat
iafox chat %*
