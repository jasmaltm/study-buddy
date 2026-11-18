<#
.SYNOPSIS
    Starts the AI Study Buddy API and opens its local web interface.
#>

$ErrorActionPreference = "Stop"
$port = 8000
if (-not [string]::IsNullOrWhiteSpace($env:PORT)) {
    $configuredPort = 0
    if (-not [int]::TryParse($env:PORT, [ref]$configuredPort) -or
        $configuredPort -lt 1 -or $configuredPort -gt 65535) {
        throw "PORT must be an integer between 1 and 65535."
    }
    $port = $configuredPort
}
$serverUrl = "http://127.0.0.1:$port"
$healthUrl = "$serverUrl/api/health"
$provider = $env:REAL_LLM_PROVIDER
if ([string]::IsNullOrWhiteSpace($provider)) {
    $provider = "ollama"
}
$provider = $provider.Trim().ToLowerInvariant()
$useFake = "$env:USE_FAKE_LLM".Trim().ToLowerInvariant() -eq "true"

if (-not $useFake -and
    ($provider.Trim().ToLowerInvariant() -eq "gemini") -and
    [string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
    $secureKey = Read-Host "Enter your Gemini API key (input hidden)" -AsSecureString
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    try {
        $env:GEMINI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
        $secureKey.Dispose()
    }

    if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
        throw "A Gemini API key is required. Create one at https://aistudio.google.com/app/apikey."
    }
}

$serverReady = $false
$health = $null
try {
    $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
} catch {
    $health = $null
}

if ($health -and $health.ok -eq $true) {
    $serverReady = $true
    $actualProvider = [string]$health.provider
    $actualFake = [bool]$health.fake_llm
    if ($actualProvider -ne $provider -or $actualFake -ne $useFake) {
        throw "A server is already running with provider '$actualProvider' (fake mode: $actualFake). Stop it, then run this launcher again for '$provider' (fake mode: $useFake)."
    }
    Write-Host "Using the existing AI Study Buddy server at $serverUrl"
} else {
    Write-Host "Starting the AI Study Buddy server..."
}

if (-not $serverReady) {
    $python = Get-Command python -ErrorAction Stop
    Start-Process -FilePath $python.Source `
        -ArgumentList "api_server.py" `
        -WorkingDirectory $PSScriptRoot

    $lastError = $null
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
            if ($health.ok -eq $true) {
                $serverReady = $true
                break
            }
        } catch {
            $lastError = $_
        }
        Start-Sleep -Seconds 1
    }

    if (-not $serverReady) {
        $detail = if ($lastError) { $lastError.Exception.Message } else { "Health check returned an unexpected response." }
        throw "AI Study Buddy did not start at $serverUrl. $detail"
    }
}

Start-Process -FilePath $serverUrl
Write-Host "AI Study Buddy is ready at $serverUrl"
