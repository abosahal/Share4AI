# Maintainer-only install/reinstall/uninstall smoke test. Never an end-user step.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$testDir = [IO.Path]::GetFullPath((Join-Path $repoRoot '.state/installed-trial'))
if (-not $testDir.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test directory' }
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{A9FDF7E6-C713-4BDB-9E40-97E82454E0EE}_is1'
$desktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Share4AI.lnk'
$startLink = Join-Path ([Environment]::GetFolderPath('Programs')) 'Share4AI.lnk'
if ((Test-Path -LiteralPath $uninstallKey) -or (Test-Path -LiteralPath $desktopLink) -or (Test-Path -LiteralPath $startLink) -or (Test-Path -LiteralPath $testDir)) {
    throw 'An installation or shortcut already exists; do not overwrite it during testing'
}
$setupFile = Join-Path $repoRoot 'dist/installer/Share4AI-Setup-1.1.4-windows-x64.exe'
$report = Join-Path $repoRoot 'build/installed-smoke.json'
try {
    foreach ($attempt in 1..3) {
        $setupArguments = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/DIR="' + $testDir + '"'))
        if ($attempt -eq 1) { $setupArguments += '/TASKS=""' }
        if ($attempt -eq 2) { $setupArguments += '/TASKS="desktopicon"' }
        $setupProcess = Start-Process -FilePath $setupFile -ArgumentList $setupArguments -WindowStyle Hidden -Wait -PassThru
        if ($setupProcess.ExitCode -ne 0) { throw 'Installation failed' }
        if (-not (Test-Path -LiteralPath $startLink)) { throw 'Start menu shortcut missing' }
        if ((Test-Path -LiteralPath $desktopLink) -ne ($attempt -gt 1)) { throw 'Desktop shortcut option was not respected' }
        if (-not (Test-Path -LiteralPath (Join-Path $testDir '_internal/python312.dll'))) { throw 'Bundled Python missing' }
        $env:PATH = Join-Path $env:SystemRoot 'System32'
        $env:PYTHONHOME = $null
        $env:PYTHONPATH = $null
        $env:TCL_LIBRARY = $null
        $env:TK_LIBRARY = $null
        if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report }
        $appProcess = Start-Process -FilePath (Join-Path $testDir 'Share4AI.exe') -ArgumentList @('--smoke-test',('"' + $report + '"')) -WindowStyle Hidden -PassThru
        if (-not $appProcess.WaitForExit(45000)) { $appProcess.Kill(); throw 'Installed app timed out' }
        if ($appProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $report)) { throw 'Installed app failed' }
        $result = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        if (-not $result.ok) { throw 'Installed app check failed' }
    }
} finally {
    $uninstaller = Join-Path $testDir 'unins000.exe'
    if (Test-Path -LiteralPath $uninstaller) {
        $uninstallProcess = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -WindowStyle Hidden -Wait -PassThru
        if ($uninstallProcess.ExitCode -ne 0) { throw 'Uninstall failed' }
    }
}
if ((Test-Path -LiteralPath $desktopLink) -or (Test-Path -LiteralPath $startLink) -or (Test-Path -LiteralPath $uninstallKey)) { throw 'Uninstall cleanup incomplete' }
Write-Output 'Install, reinstall, bundled UI without Python on PATH, and uninstall passed.'
