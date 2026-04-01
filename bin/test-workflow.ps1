# Quick workflow smoke test for Windows PowerShell

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    return @()
}

function Invoke-Python {
    param(
        [string[]]$PythonCommand,
        [string[]]$Arguments
    )

    $exe = $PythonCommand[0]
    $baseArgs = if ($PythonCommand.Count -gt 1) { $PythonCommand[1..($PythonCommand.Count - 1)] } else { @() }
    $argumentList = @()
    if ($baseArgs.Count -gt 0) {
        $argumentList += $baseArgs
    }
    if ($Arguments.Count -gt 0) {
        $argumentList += $Arguments
    }

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()

    try {
        $process = Start-Process -FilePath $exe -ArgumentList $argumentList -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
        $global:LASTEXITCODE = $process.ExitCode

        $stdout = if ((Get-Item $stdoutFile).Length -gt 0) { Get-Content $stdoutFile -Raw -Encoding UTF8 } else { "" }
        $stderr = if ((Get-Item $stderrFile).Length -gt 0) { Get-Content $stderrFile -Raw -Encoding UTF8 } else { "" }

        return [PSCustomObject]@{
            ExitCode = $process.ExitCode
            StdOut = $stdout.Trim()
            StdErr = $stderr.Trim()
        }
    }
    finally {
        Remove-Item $stdoutFile, $stderrFile -ErrorAction SilentlyContinue
    }
}

$pythonCommand = Get-PythonCommand

Write-Output "=== Video Breakdown Workflow Smoke Test ==="
Write-Output ""

Write-Output "[1/5] Checking Python..."
if ($pythonCommand.Count -eq 0) {
    Write-Output "ERROR: Python was not found"
    exit 1
}
$pythonVersion = Invoke-Python -PythonCommand $pythonCommand -Arguments @("--version")
if ($pythonVersion.ExitCode -ne 0) {
    Write-Output "ERROR: Could not run Python"
    if ($pythonVersion.StdErr) {
        Write-Output $pythonVersion.StdErr
    }
    exit 1
}
if ($pythonVersion.StdOut) {
    Write-Output $pythonVersion.StdOut
}
Write-Output "[OK] Python is available"

Write-Output ""
Write-Output "[2/5] Checking dependencies..."
$dependencyCheck = Invoke-Python -PythonCommand $pythonCommand -Arguments @("-c", "__import__('google.genai')")
if ($dependencyCheck.ExitCode -eq 0) {
    Write-Output "[OK] google-genai"
} else {
    Write-Output "[WARN] google-genai is not installed"
    if ($dependencyCheck.StdErr) {
        Write-Output $dependencyCheck.StdErr
    }
}

if (Get-Command yt-dlp -ErrorAction SilentlyContinue) {
    Write-Output "[OK] yt-dlp"
} else {
    Write-Output "[WARN] yt-dlp is not installed"
}

Write-Output ""
Write-Output "[3/5] Checking API key..."
if ($env:GEMINI_API_KEY) {
    Write-Output "[OK] GEMINI_API_KEY is set"
} else {
    Write-Output "[WARN] GEMINI_API_KEY is not set"
}

Write-Output ""
Write-Output "[4/5] Running generate + validate smoke test..."
$analysisFile = Join-Path $projectDir "output\analysis-final.json"
$smokeOutput = Join-Path $env:TEMP "video-breakdown-smoke.md"

if (-not (Test-Path $analysisFile)) {
    Write-Output "[WARN] analysis-final.json not found, skipping generate + validate test"
} else {
    $generateResult = Invoke-Python -PythonCommand $pythonCommand -Arguments @(
        (Join-Path $projectDir "bin\generate-prompts.py"),
        $analysisFile,
        "--output",
        $smokeOutput
    )
    if ($generateResult.ExitCode -ne 0) {
        Write-Output "[FAIL] generate-prompts.py failed"
        if ($generateResult.StdErr) {
            Write-Output $generateResult.StdErr
        }
        exit 1
    }

    $validateResult = Invoke-Python -PythonCommand $pythonCommand -Arguments @(
        (Join-Path $projectDir "bin\validate-output.py"),
        "breakdown",
        $smokeOutput
    )
    if ($validateResult.ExitCode -eq 0) {
        Write-Output "[OK] Generated markdown passed validation"
    } else {
        Write-Output "[FAIL] Generated markdown failed validation"
        if ($validateResult.StdErr) {
            Write-Output $validateResult.StdErr
        }
        exit 1
    }

    Remove-Item $smokeOutput -ErrorAction SilentlyContinue
}

Write-Output ""
Write-Output "[5/5] Checking template files..."
$templateChecks = @(
    @{ Path = Join-Path $projectDir "templates\prompt-template.md"; Name = "Professional template" },
    @{ Path = Join-Path $projectDir "templates\gemini-prompt-v2.txt"; Name = "Gemini prompt (v2)" }
)

foreach ($check in $templateChecks) {
    if (Test-Path $check.Path) {
        Write-Output "[OK] $($check.Name)"
    } else {
        Write-Output "[FAIL] Missing: $($check.Name)"
        exit 1
    }
}

Write-Output ""
Write-Output "=== Smoke test complete ==="
