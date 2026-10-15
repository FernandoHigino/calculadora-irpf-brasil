$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
	throw "uv not found. Install uv to build the executable."
}

$arguments = @(
	"run", "--python", "3.12", "--with", "pyinstaller", "pyinstaller",
	"--noconfirm", "--clean", "--onefile", "--console",
	"--name", "CalculadoraIRPF",
	"--paths", $projectRoot,
	"--add-data", "$projectRoot\src\dados\tabelas_ir.json;src\dados",
	"--distpath", "$projectRoot\dist",
	"--workpath", "$projectRoot\build",
	"--specpath", "$projectRoot\build",
	"$projectRoot\src\main.py"
)

& uv @arguments
if ($LASTEXITCODE -ne 0) {
	throw "Build failed."
}

Write-Output "Executable created: $projectRoot\dist\CalculadoraIRPF.exe"