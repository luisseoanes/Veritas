# Arranque del backend en Windows (B13). Equivalente a run.sh.
#
# Idempotente: crea el venv si falta, instala deps, copia .env desde el ejemplo
# la primera vez y levanta la API. Correr desde la raiz del repo:  .\run.ps1
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Venv = ".venv"
$Py = Join-Path $Venv "Scripts\python.exe"

# 1) venv
if (-not (Test-Path $Venv)) {
    Write-Host "==> Creando entorno virtual en $Venv"
    python -m venv $Venv
}

# 2) dependencias
Write-Host "==> Instalando dependencias"
& $Py -m pip install --quiet --upgrade pip
& $Py -m pip install --quiet -r requirements.txt

# 3) .env
if (-not (Test-Path ".env")) {
    Write-Host "==> No hay .env; copiando desde .env.example"
    Copy-Item ".env.example" ".env"
    Write-Host "!!  Edita .env y define ADMIN_TOKEN antes de la demo (el proceso no"
    Write-Host "!!  levanta con ADMIN_TOKEN vacio). Genera uno con:"
    Write-Host "!!    $Py -c ""import secrets; print(secrets.token_urlsafe(24))"""
}

# 4) API
$BindHost = if ($env:HOST) { $env:HOST } else { "127.0.0.1" }
$Port = if ($env:PORT) { $env:PORT } else { "8000" }
Write-Host "==> Levantando API en http://${BindHost}:${Port} (docs en /docs)"
& $Py -m uvicorn app.main:app --reload --host $BindHost --port $Port
