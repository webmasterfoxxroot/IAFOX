@echo off
chcp 65001 >nul
title IAFOX - Instalacao

echo ========================================
echo     IAFOX - Instalacao Windows
echo ========================================
echo.

REM Verifica Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK: Python encontrado

REM Verifica Ollama
echo [2/4] Verificando Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama nao encontrado.
    echo Baixe em: https://ollama.com/download
    echo Apos instalar, execute este script novamente.
    pause
    exit /b 1
)
echo OK: Ollama encontrado

REM Cria ambiente virtual
echo [3/4] Criando ambiente virtual...
if not exist ".venv" (
    python -m venv .venv
)
echo OK: Ambiente virtual criado

REM Instala dependencias
echo [4/4] Instalando dependencias...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -e ".[dev]"
echo OK: Dependencias instaladas

echo.
echo ========================================
echo     INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Para iniciar:
echo   1. Execute: start_cli.bat (terminal)
echo   2. Execute: start_web.bat (navegador)
echo.
pause
