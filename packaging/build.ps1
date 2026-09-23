$ErrorActionPreference = 'Stop'

$PackagingDir = $PSScriptRoot
$ProjectRoot = Split-Path $PackagingDir -Parent
$DistDir = Join-Path $ProjectRoot 'dist'
$BuildDir = Join-Path $ProjectRoot 'build'
$Python = Join-Path $PackagingDir 'env\Scripts\python.exe'
$SpecFile = Join-Path $PackagingDir 'TimeSync.spec'
$InstallerScript = Join-Path $PackagingDir '.\TimeSyncCompiler.iss'

if (-not (Test-Path $Python)) {
	& python -m venv (Join-Path $PackagingDir 'env')
}

& $Python -m pip install -r (Join-Path $PackagingDir 'requirements.txt')


Push-Location $ProjectRoot
if (Test-Path $DistDir) {
	Remove-Item $DistDir -Recurse -Force
}
if (Test-Path $BuildDir) {
	Remove-Item $BuildDir -Recurse -Force
}


try {
	& $Python -m PyInstaller $SpecFile --clean
}
finally {
	Pop-Location
}


$InnoSetup = @(
	'C:\Program Files (x86)\Inno Setup 7\ISCC.exe',
	'C:\Program Files\Inno Setup 7\ISCC.exe'
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $InnoSetup) {
	throw 'Inno Setup 7 was not found.'
}

& $InnoSetup $InstallerScript