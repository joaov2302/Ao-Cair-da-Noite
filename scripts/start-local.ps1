$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Instale as dependências conforme README.md.' }
$logDirectory = Join-Path $projectRoot 'local-logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$backendProcess = $null
$frontendProcess = $null
if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    $backendProcess = Start-Process -FilePath $pythonPath -ArgumentList 'manage.py','runserver','127.0.0.1:8000','--noreload' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'backend.log') -RedirectStandardError (Join-Path $logDirectory 'backend-error.log')
}
if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 5173 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    $nodePath = (Get-Command node.exe).Source
    $vitePath = Join-Path $projectRoot 'frontend\node_modules\vite\bin\vite.js'
    if (-not (Test-Path -LiteralPath $vitePath)) { throw 'Instale o frontend conforme README.md.' }
    $frontendProcess = Start-Process -FilePath $nodePath -ArgumentList ('"'+$vitePath+'"'),'--host','127.0.0.1' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'frontend.log') -RedirectStandardError (Join-Path $logDirectory 'frontend-error.log')
}
Write-Output ('Backend iniciado nesta chamada: '+$backendProcess.Id)
Write-Output ('Frontend iniciado nesta chamada: '+$frontendProcess.Id)
Write-Output 'Acesse http://127.0.0.1:5173'
