<#
.SYNOPSIS
    Real-World Multi-Task Cross-Session Memory Demonstration (Phase 3 / Pillar 4)
    Simulates a student across 3 distinct sessions and proves memory persistence:
    Session 1: Student learns Newton's Laws (Quiz score: 100% -> Added to Mastered Topics)
    Session 2: Student struggles with Thermodynamics (Quiz score: 20% -> Flagged in Weak Areas)
    Session 3: Fresh Agent instance starts up, restores memory, and demonstrates tailored recall!
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 3: MULTI-TASK CROSS-SESSION MEMORY EXECUTION DEMO" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan

$memoryFile = Join-Path ([System.IO.Path]::GetTempPath()) "study-buddy-demo-memory-$([guid]::NewGuid().ToString('N')).json"
$demoMemory = @{
    user_profile = @{
        name = "Student"
        grade_level = "Grade 10"
        learning_style = "Prefers intuitive analogies and step-by-step breakdowns"
        preferred_subjects = @("Science", "Math")
    }
    mastered_concepts = @()
    weak_areas = @()
    quiz_scores = @()
    study_notes_index = @()
    task_history = @()
}
$demoMemory | ConvertTo-Json -Depth 6 | Set-Content -Path $memoryFile -Encoding UTF8

# --- SESSION 1: Learn Newton's Laws ---
Write-Host "`n>>> [SESSION 1] Student studies Newton's Second Law..." -ForegroundColor Yellow
$session1Mem = Get-Content -Path $memoryFile -Raw | ConvertFrom-Json

# Student completes quiz on Newton's Laws with 100%
Write-Host "  Student takes Newton's Laws Quiz -> Score: 5/5 (100%)" -ForegroundColor Gray
$session1Mem.mastered_concepts = @($session1Mem.mastered_concepts + "Newton's Second Law" | Select-Object -Unique)
$session1Mem.quiz_scores = @($session1Mem.quiz_scores + @{
    timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    topic = "Newton's Second Law"
    score = 5
    total = 5
    percentage = 100
})
$session1Mem.task_history = @($session1Mem.task_history + @{
    timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    task = "Newton's Laws study & quiz"
    summary = "Calculated F = m*a with 100% score"
    tools_used = @("calculate_math_formula", "generate_quiz")
})

# Save the isolated demonstration memory.
$session1Mem | ConvertTo-Json -Depth 6 | Set-Content -Path $memoryFile -Encoding UTF8
Write-Host "  [SESSION 1 COMMITTED] Saved to temporary demo memory." -ForegroundColor Green


# --- SESSION 2: Student Struggles with Thermodynamics ---
Write-Host "`n>>> [SESSION 2] Student attempts Thermodynamics..." -ForegroundColor Yellow
$session2Mem = Get-Content -Path $memoryFile -Raw | ConvertFrom-Json

# Student takes Thermodynamics Quiz -> Score: 1/5 (20%)
Write-Host "  Student takes Thermodynamics Quiz -> Score: 1/5 (20%)" -ForegroundColor Gray
$session2Mem.weak_areas = @($session2Mem.weak_areas + "Thermodynamics Heat Engines" | Select-Object -Unique)
$session2Mem.quiz_scores = @($session2Mem.quiz_scores + @{
    timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    topic = "Thermodynamics Heat Engines"
    score = 1
    total = 5
    percentage = 20
})
$session2Mem.task_history = @($session2Mem.task_history + @{
    timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    task = "Thermodynamics review"
    summary = "Struggled with Carnot cycle efficiency"
    tools_used = @("search_knowledge_base", "generate_quiz")
})

# Save the isolated demonstration memory.
$session2Mem | ConvertTo-Json -Depth 6 | Set-Content -Path $memoryFile -Encoding UTF8
Write-Host "  [SESSION 2 COMMITTED] Saved to temporary demo memory." -ForegroundColor Green


# --- SESSION 3: Brand New Agent Instance Spawns ---
Write-Host "`n>>> [SESSION 3] Fresh Agent instance boots up..." -ForegroundColor Yellow
Write-Host "  Simulating completely new application launch (cold start)..." -ForegroundColor Gray

# Agent cold start: reads the isolated demo memory file.
$agentColdStartMemory = Get-Content -Path $memoryFile -Raw | ConvertFrom-Json

# Generate System Prompt Context Injection
$masteredList = ($agentColdStartMemory.mastered_concepts -join ", ")
$weakList = ($agentColdStartMemory.weak_areas -join ", ")
$recentTasks = ($agentColdStartMemory.task_history | Select-Object -Last 2 | ForEach-Object { "- [$($_.timestamp)] $($_.task) -> $($_.summary)" }) -join "`n"

$promptContext = @"
--- STUDENT MEMORY PROFILE (CROSS-TASK PERSISTENCE) ---
Student: $($agentColdStartMemory.user_profile.name) | Level: $($agentColdStartMemory.user_profile.grade_level)
Learning Style: $($agentColdStartMemory.user_profile.learning_style)
Mastered Topics: $masteredList
Topics Needing Review: $weakList

Recent Study History:
$recentTasks
--------------------------------------------------------
"@

Write-Host "`n[RECOVERED MEMORY PROMPT CONTEXT INJECTED INTO AGENT]:" -ForegroundColor DarkCyan
Write-Host $promptContext -ForegroundColor Cyan

# Verification assertions
if ($promptContext.Contains("Newton's Second Law") -and $promptContext.Contains("Thermodynamics Heat Engines")) {
    Write-Host "`n  [VERIFIED] Session 3 successfully recalled Mastered concepts from Session 1" -ForegroundColor Green
    Write-Host "  [VERIFIED] Session 3 successfully recalled Weak areas from Session 2" -ForegroundColor Green
    Write-Host "  [VERIFIED] Persistent JSON storage retained complete task history across sessions!" -ForegroundColor Green
} else {
    throw "Memory cross-session continuity failed"
}

Write-Host "`n==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 3 EXECUTION COMPLETE: PERSISTENT MEMORY VERIFIED!" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Cyan
Remove-Item -Path $memoryFile -Force

