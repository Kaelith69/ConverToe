Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot

$isccCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue

$candidates = @()

if ($isccCommand) {
    $candidates += $isccCommand.Source
}

$candidates += Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
$candidates += 'C:\Program Files\Inno Setup 6\ISCC.exe'
$candidates += 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'

$iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    throw 'ISCC.exe was not found. Install Inno Setup to build the installer.'
}

& $iscc '.\ConverToe.iss'