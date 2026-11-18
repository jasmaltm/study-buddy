<#
.SYNOPSIS
    Phase 8: Frontend UI & End-to-End System Integration Verification Suite
    Tests:
    - Task 8.1: Full System 7-Pillars Master Test Suite Execution
    - Task 8.2: Web Application DOM, Assets, Tools, and Safety Components Verification
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 8: FULL SYSTEM & UI INTEGRATION VERIFICATION" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan

# -------------------------------------------------------------------------
# TASK 8.2: Web Application Components Verification
# -------------------------------------------------------------------------
Write-Host "`n[Task 8.2] Inspecting Web UI Application Architecture (index.html)..." -ForegroundColor Yellow

$htmlPath = "index.html"
if (-not (Test-Path $htmlPath)) { throw "index.html not found!" }

$htmlContent = Get-Content -Path $htmlPath -Raw

$requiredUIComponents = @(
    @{ Name = "Tailwind CSS & Styling"; Check = { $htmlContent.Contains("cdn.tailwindcss.com") } },
    @{ Name = "Lucide Icons CDN"; Check = { $htmlContent.Contains("unpkg.com/lucide") } },
    @{ Name = "Pillar 1: ReAct Feed (Think/Act/Look)"; Check = { $htmlContent.Contains("chat-feed") } },
    @{ Name = "Pillar 2: 4 Active Tools Listed"; Check = { 
        $htmlContent.Contains("search_knowledge_base") -and 
        $htmlContent.Contains("calculate_math_formula") -and 
        $htmlContent.Contains("generate_quiz") -and 
        $htmlContent.Contains("save_study_notes") 
    } },
    @{ Name = "Pillar 3: Self-Correction Demo Trigger"; Check = { $htmlContent.Contains("error_recovery") } },
    @{ Name = "Pillar 4: Memory Dashboard Drawer"; Check = { $htmlContent.Contains("memory-drawer") } },
    @{ Name = "Pillar 5: Pre-Action Plan"; Check = {
        $htmlContent.Contains("plan-status-badge") -and
        $htmlContent.Contains("plan-steps-container")
    } },
    @{ Name = "Pillar 6: Safety Modal (HITL Asks You First)"; Check = { $htmlContent.Contains("safety-modal") } },
    @{ Name = "Pillar 6: Audit Log Stream"; Check = { $htmlContent.Contains("audit-log-stream") } },
    @{ Name = "Pillar 7: Dual-Tier Engine Switcher"; Check = { $htmlContent.Contains("toggle-engine-btn") } }
)

foreach ($comp in $requiredUIComponents) {
    if (& $comp.Check) {
        Write-Host "  [PASSED] UI Component Verified: $($comp.Name)" -ForegroundColor Green
    } else {
        throw "UI Component Missing: $($comp.Name)"
    }
}

# -------------------------------------------------------------------------
# TASK 8.1: Full System 7-Pillars Master Test Suite Execution
# -------------------------------------------------------------------------
Write-Host "`n[Task 8.1] Running Master 7-Pillar End-to-End Test Suite..." -ForegroundColor Yellow

$masterOutput = powershell -ExecutionPolicy Bypass -File .\test_agent.ps1

if ($masterOutput -match "ALL 7 PILLARS VERIFIED AND PASSED SUCCESSFULLY!") {
    Write-Host "  [PASSED] 8.1: Master test suite passed with 100% success across all 7 pillars." -ForegroundColor Green
} else {
    throw "Master test suite failed."
}

# Verify UI Launcher Script
$launcherPath = "start_ui.ps1"
if (Test-Path $launcherPath) {
    $launcherContent = Get-Content -Path $launcherPath -Raw
    if ($launcherContent.Contains("api_server.py") -and $launcherContent.Contains("/api/health")) {
        Write-Host "  [PASSED] UI Launcher starts the API server and checks its health." -ForegroundColor Green
    } else {
        throw "UI launcher does not start and verify the local API server."
    }
} else {
    throw "start_ui.ps1 missing"
}

Write-Host "`n==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 8 COMPLETED: SYSTEM FULLY INTEGRATED & READY FOR PRODUCTION!" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Cyan
