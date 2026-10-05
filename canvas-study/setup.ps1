param(
  [ValidateSet('codex','claude','openclaw','generic')][string]$HostName,
  [ValidateSet('auto','api','browser')][string]$Mode='auto',
  [string]$DataRoot=(Join-Path $env:USERPROFILE 'CanvasStudy'),
  [switch]$Apply
)
$ErrorActionPreference='Stop'
if (-not $HostName) { $HostName=Read-Host 'Host (codex / claude / openclaw / generic)' }
if ($HostName -notin @('codex','claude','openclaw','generic')) { throw 'Unsupported host' }
$python=Get-Command python.exe -ErrorAction SilentlyContinue
$pythonPrefix=@()
function Test-StudyPython($Command, $Prefix) {
  if (-not $Command -or $Command.Source -like '*\WindowsApps\*') { return $false }
  try {
    $null=& $Command.Source @Prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>$null
    return ($LASTEXITCODE -eq 0)
  } catch { return $false }
}
if (-not (Test-StudyPython $python @())) {
  $python=Get-Command py.exe -ErrorAction SilentlyContinue
  $pythonPrefix=@('-3')
}
if (-not (Test-StudyPython $python $pythonPrefix)) {
  if (-not $Apply) { Write-Output 'Python 3.11+ required. Apply mode can install Python 3.12 with winget for this user.'; exit 0 }
  $winget=Get-Command winget.exe -ErrorAction SilentlyContinue
  if (-not $winget) { throw 'Install Python 3.11+ from python.org, then rerun setup. No system settings were changed.' }
  & $winget.Source install --id Python.Python.3.12 --exact --scope user --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) { throw 'Python installation failed; inspect winget output.' }
  Write-Output 'Open a new terminal and rerun this command so Python is on PATH.'
  exit 0
}
$setupArgs=@((Join-Path $PSScriptRoot 'scripts\setup.py'),'--host',$HostName,'--mode',$Mode,'--root',$DataRoot)
if ($Apply) { $setupArgs+='--apply' }
& $python.Source @pythonPrefix @setupArgs
exit $LASTEXITCODE
