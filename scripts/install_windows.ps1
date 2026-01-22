# IAFOX - Script de Instalacao para Windows
# Execute como Administrador

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    IAFOX - Instalacao Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica Python
Write-Host "[1/5] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Python nao encontrado!" -ForegroundColor Red
    Write-Host "Baixe em: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host "OK: $pythonVersion" -ForegroundColor Green

# Verifica Ollama
Write-Host "[2/5] Verificando Ollama..." -ForegroundColor Yellow
$ollamaVersion = ollama --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ollama nao encontrado. Deseja instalar? (S/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "S" -or $response -eq "s") {
        Write-Host "Baixando Ollama..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "$env:TEMP\OllamaSetup.exe"
        Start-Process "$env:TEMP\OllamaSetup.exe" -Wait
    }
} else {
    Write-Host "OK: Ollama instalado" -ForegroundColor Green
}

# Cria ambiente virtual
Write-Host "[3/5] Criando ambiente virtual..." -ForegroundColor Yellow
$venvPath = ".venv"
if (!(Test-Path $venvPath)) {
    python -m venv $venvPath
}
Write-Host "OK: Ambiente virtual criado" -ForegroundColor Green

# Ativa ambiente e instala dependencias
Write-Host "[4/5] Instalando dependencias..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -e ".[dev]"
Write-Host "OK: Dependencias instaladas" -ForegroundColor Green

# Baixa modelo
Write-Host "[5/5] Baixando modelo de IA..." -ForegroundColor Yellow
Write-Host "Modelos recomendados para sua RTX 4090 (24GB):" -ForegroundColor Cyan
Write-Host "  1. qwen2.5-coder:32b (Recomendado - melhor qualidade)"
Write-Host "  2. qwen2.5-coder:14b (Mais rapido)"
Write-Host "  3. deepseek-coder-v2:16b (Alternativa)"
Write-Host ""
$modelChoice = Read-Host "Escolha o modelo (1/2/3) ou digite o nome"

switch ($modelChoice) {
    "1" { $model = "qwen2.5-coder:32b" }
    "2" { $model = "qwen2.5-coder:14b" }
    "3" { $model = "deepseek-coder-v2:16b" }
    default { $model = $modelChoice }
}

Write-Host "Baixando $model... (isso pode demorar)" -ForegroundColor Cyan
ollama pull $model

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "    INSTALACAO CONCLUIDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar o IAFOX:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  CLI (terminal):" -ForegroundColor Cyan
Write-Host "    .venv\Scripts\Activate.ps1"
Write-Host "    iafox chat"
Write-Host ""
Write-Host "  Web (navegador):" -ForegroundColor Cyan
Write-Host "    .venv\Scripts\Activate.ps1"
Write-Host "    python -m iafox.web.api"
Write-Host "    Acesse: http://localhost:8000"
Write-Host ""
