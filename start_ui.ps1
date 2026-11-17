<#
.SYNOPSIS
    Launcher for AI Study Buddy Web UI (Phase 8 / Task 8.2)
    Opens the interactive 7-Pillar AI Study Buddy application in your default web browser.
#>

$uiPath = Join-Path $PSScriptRoot "index.html"

if (Test-Path $uiPath) {
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "   LAUNCHING AI STUDY BUDDY WEB APPLICATION" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "Opening in default browser: $uiPath" -ForegroundColor Green
    Start-Process $uiPath
    Write-Host "`nApp active! You can interactively test all 7 Pillars in the web interface:" -ForegroundColor Yellow
    Write-Host "  1. Loop: Think -> Act -> Look live stepper" -ForegroundColor DarkCyan
    Write-Host "  2. 4 Active Tools: Knowledge Base, Math Calculator, Quiz, Save Notes" -ForegroundColor DarkCyan
    Write-Host "  3. Self-Healing: Click 'Self-Correction (Pillar 3)' quick demo" -ForegroundColor DarkCyan
    Write-Host "  4. Memory Dashboard: Click 'Memory' in top nav to inspect persisted profile" -ForegroundColor DarkCyan
    Write-Host "  5. Pre-Action Plan: Visible dynamic roadmap banner" -ForegroundColor DarkCyan
    Write-Host "  6. Safety Gate: Human-in-the-loop modal prompts before saving notes" -ForegroundColor DarkCyan
    Write-Host "  7. Engine Switcher: Toggle between Fake LLM and Real LLM (Gemini)" -ForegroundColor DarkCyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
} else {
    Write-Error "Could not find index.html at $uiPath"
}

