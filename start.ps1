$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath $PSScriptRoot
$env:ADMIN_PASSWORD = 'Alibaba128!'
$env:HOST = '127.0.0.1'
$env:PORT = '9000'

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 app.py
} else {
    python app.py
}
