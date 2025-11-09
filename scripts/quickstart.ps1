$ErrorActionPreference = "Stop"
Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
python -m venv venv
Write-Host "Activando entorno..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1
Write-Host "Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip
Write-Host "Instalando dependencias..." -ForegroundColor Cyan
pip install -r requirements.txt
Write-Host "Iniciando aplicación..." -ForegroundColor Green
python main.py