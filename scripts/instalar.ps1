# Instala o Facilita Studio no Windows (PowerShell).
#   powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1 -Teste
param([switch]$Teste)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$Raiz = Get-Location
Write-Host "== Facilita Studio: instalação em $Raiz"

# 1. Python 3.10+
$py = $null
foreach ($c in @("py -3.13", "py -3.12", "py -3.11", "py -3.10", "python")) {
  $partes = $c.Split(" ")
  try {
    & $partes[0] $partes[1..9] -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $partes; break }
  } catch {}
}
if (-not $py) { Write-Host "Preciso do Python 3.10+: winget install Python.Python.3.12"; exit 1 }

# 2. ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Host "ffmpeg não encontrado. Instale com: winget install Gyan.FFmpeg  (depois feche e abra o terminal)"
  exit 1
}

# 3. Ambiente Python isolado em .venv
if (-not (Test-Path .venv)) { & $py[0] $py[1..9] -m venv .venv }
& .venv\Scripts\python.exe -m pip install -q --upgrade pip
& .venv\Scripts\python.exe -m pip install -q -e ".[dev]"

# 4. Chromium do Playwright (com CHROMIUM_PATH definido, usa esse navegador)
if (-not $env:CHROMIUM_PATH) {
  & .venv\Scripts\python.exe -m playwright install chromium
  if ($LASTEXITCODE -ne 0) { Write-Host "AVISO: não baixei o Chromium. Rode depois: .venv\Scripts\python.exe -m playwright install chromium" }
}

# 5. Pastas de trabalho
New-Item -ItemType Directory -Force -Path projetos, saida | Out-Null

Write-Host "`n== Conferindo a marca"
& .venv\Scripts\facilita.exe marca

if ($Teste) {
  & .venv\Scripts\python.exe exemplos\gerar_amostras.py
  $M = "exemplos\amostras\marca-teste"
  & .venv\Scripts\facilita.exe --marca $M imagem exemplos\oferta-xcaret.yaml --formato feed --formato story --permitir-fonte-substituta
  & .venv\Scripts\facilita.exe --marca $M cobertura exemplos\xcaret-arte\roteiro.md --clips exemplos\xcaret-arte\clips.yaml
  Write-Host "Teste ok. Imagens em saida\imagens\."
}

Write-Host @"

Pronto. Para usar, em cada terminal novo:
  cd "$Raiz"
  .venv\Scripts\Activate.ps1
  facilita novo "Xcaret Arte"
  facilita --help
"@
