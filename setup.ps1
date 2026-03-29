#!/usr/bin/env pwsh
# setup.ps1 - Install dependencies for the video breakdown skill.
# Usage: powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = 'Stop'

function Invoke-ArrayCommand {
    param([string[]]$Command)

    if ($Command.Count -eq 0) {
        throw 'Empty command'
    }

    if ($Command.Count -eq 1) {
        & $Command[0]
        return
    }

    & $Command[0] $Command[1..($Command.Count - 1)]
}

function Resolve-PythonCommand {
    $candidates = @(
        @('py', '-3'),
        @('python'),
        @('python3')
    )

    foreach ($candidate in $candidates) {
        try {
            Invoke-ArrayCommand ($candidate + @('--version')) *> $null
            return ,$candidate
        } catch {
            continue
        }
    }

    return $null
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonCommand = Resolve-PythonCommand
$errors = 0

Write-Host '=========================================='
Write-Host '  Video Breakdown Skill - Dependency Setup'
Write-Host '=========================================='
Write-Host ''

Write-Host '[1/3] Checking Python...'
if ($null -ne $pythonCommand) {
    $pythonVersion = (Invoke-ArrayCommand ($pythonCommand + @('--version')) 2>&1 | Out-String).Trim()
    Write-Host "  Found: $pythonVersion"

    $versionCheck = @(
        'import sys',
        'major, minor = sys.version_info[:2]',
        'print(f"{major}.{minor}")',
        'raise SystemExit(0 if (major, minor) >= (3, 8) else 1)'
    ) -join "`n"

    try {
        $detectedVersion = (Invoke-ArrayCommand ($pythonCommand + @('-c', $versionCheck)) | Out-String).Trim()
    } catch {
        $detectedVersion = 'unknown'
        Write-Host "  WARNING: Python 3.8+ is required, current version is $detectedVersion"
        Write-Host '  Download: https://www.python.org/downloads/'
        $errors++
    }
} else {
    Write-Host '  ERROR: Python 3.8+ was not found.'
    Write-Host '  Download: https://www.python.org/downloads/'
    $errors++
}

Write-Host ''
Write-Host '[2/3] Installing Python packages...'
$requirementsFile = Join-Path $scriptDir 'requirements.txt'
if ($null -ne $pythonCommand) {
    try {
        if (Test-Path $requirementsFile) {
            Invoke-ArrayCommand ($pythonCommand + @('-m', 'pip', 'install', '--user', '-r', $requirementsFile, '--quiet')) *> $null
        } else {
            Invoke-ArrayCommand ($pythonCommand + @('-m', 'pip', 'install', '--user', 'google-genai', '--quiet')) *> $null
        }
        Write-Host '  Python packages installed.'
    } catch {
        Write-Host '  ERROR: Failed to install Python packages. Run this manually:'
        Write-Host "    $($pythonCommand -join ' ') -m pip install -r requirements.txt"
        $errors++
    }
} else {
    Write-Host '  ERROR: Python is missing, so package installation was skipped.'
    $errors++
}

Write-Host ''
Write-Host '[3/3] Checking yt-dlp...'
if (Get-Command yt-dlp -ErrorAction SilentlyContinue) {
    $ytVersion = (yt-dlp --version 2>&1 | Out-String).Trim()
    Write-Host "  Found: yt-dlp $ytVersion"
} elseif ($null -ne $pythonCommand) {
    Write-Host '  yt-dlp not found, installing...'
    try {
        Invoke-ArrayCommand ($pythonCommand + @('-m', 'pip', 'install', '--user', 'yt-dlp', '--quiet')) *> $null
        Write-Host '  yt-dlp installed.'
    } catch {
        Write-Host '  ERROR: Failed to install yt-dlp. Run this manually:'
        Write-Host "    $($pythonCommand -join ' ') -m pip install yt-dlp"
        $errors++
    }
} else {
    Write-Host '  ERROR: Python is missing, so yt-dlp installation was skipped.'
    $errors++
}

Write-Host ''
Write-Host '=========================================='
if ($errors -eq 0) {
    Write-Host '  Setup finished successfully.'
    Write-Host ''
    Write-Host '  Next step: configure GEMINI_API_KEY'
    Write-Host "  `$env:GEMINI_API_KEY='your-api-key'"
    Write-Host ''
    Write-Host '  API key: https://aistudio.google.com/apikey'
} else {
    Write-Host "  Setup finished with $errors issue(s)."
    Write-Host '  Review the errors above and fix them manually.'
}
Write-Host '=========================================='
