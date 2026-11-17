<#
.SYNOPSIS
    Phase 1: Environment & Project Scaffolding Verification Suite
    Tests:
    - Task 1.1: File Structure & Directory Setup
    - Task 1.2: Dependencies & Configuration Integrity
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 1: VERIFICATION OF ENVIRONMENT & SCAFFOLDING" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan

# -------------------------------------------------------------------------
# TASK 1.1: File Structure & Directory Layout
# -------------------------------------------------------------------------
Write-Host "`n[Task 1.1] Verifying Core Directory Layout..." -ForegroundColor Yellow

$requiredDirs = @(
    "agent",
    "agent/llm",
    "storage",
    "storage/notes",
    "logs",
    "tests"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  [PASSED] Directory exists: $dir" -ForegroundColor Green
    } else {
        throw "Missing required directory: $dir"
    }
}

Write-Host "`n[Task 1.1] Verifying Scaffolding Files..." -ForegroundColor Yellow

$requiredFiles = @(
    "AI_Study_Buddy_PRD.md",
    "task.md",
    "config.py",
    "run_agent.py",
    "index.html",
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "storage/memory.json",
    "agent/__init__.py",
    "agent/core.py",
    "agent/tools.py",
    "agent/memory.py",
    "agent/planner.py",
    "agent/safety.py",
    "agent/llm/__init__.py",
    "agent/llm/base.py",
    "agent/llm/fake_llm.py",
    "agent/llm/real_llm.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        $item = Get-Item $file
        Write-Host "  [PASSED] File present: $file ($($item.Length) bytes)" -ForegroundColor Green
    } else {
        throw "Missing required file: $file"
    }
}


# -------------------------------------------------------------------------
# TASK 1.2: Dependencies & Configuration Integrity
# -------------------------------------------------------------------------
Write-Host "`n[Task 1.2] Verifying Configuration Settings..." -ForegroundColor Yellow

$configContent = Get-Content -Path "config.py" -Raw

if ($configContent.Contains("USE_FAKE_LLM") -and 
    $configContent.Contains("MAX_STEPS") -and 
    $configContent.Contains("MEMORY_FILE_PATH") -and 
    $configContent.Contains("LOG_FILE_PATH")) {
    Write-Host "  [PASSED] config.py defines core parameters (MAX_STEPS, MEMORY_FILE_PATH, LOG_FILE_PATH, USE_FAKE_LLM)." -ForegroundColor Green
} else {
    throw "config.py is missing essential configuration constants."
}

# Verify .env.example contains essential keys
$envExample = Get-Content -Path ".env.example" -Raw
if ($envExample.Contains("GEMINI_API_KEY") -and $envExample.Contains("USE_FAKE_LLM")) {
    Write-Host "  [PASSED] .env.example correctly defines API key templates and environment flags." -ForegroundColor Green
} else {
    throw ".env.example is missing essential keys."
}

# Verify storage/memory.json is valid JSON
try {
    $memoryJson = Get-Content -Path "storage/memory.json" -Raw | ConvertFrom-Json
    if ($memoryJson.user_profile -and $memoryJson.mastered_concepts) {
        Write-Host "  [PASSED] storage/memory.json seeded with valid JSON schema." -ForegroundColor Green
    } else {
        throw "storage/memory.json missing required fields."
    }
} catch {
    throw "storage/memory.json contains invalid JSON: $_"
}

Write-Host "`n==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 1 COMPLETED: ALL SCAFFOLDING & CONFIGURATIONS VERIFIED!" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Cyan

