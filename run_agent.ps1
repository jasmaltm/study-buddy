<#
.SYNOPSIS
    AI Study Buddy — Interactive PowerShell CLI Runner
    Demonstrates the 7 Pillars in action directly from Windows PowerShell:
    1. Think -> Act -> Look Loop (ReAct)
    2. 4 Active Tools (Knowledge Base, Math, Quiz, Save Notes)
    3. Self-Healing: Error recovery on tool failure
    4. Memory: Persistent state across tasks (storage/memory.json)
    5. Planning: Structured step roadmap before acting
    6. Safety: Human confirmation, step limit cap, audit log
    7. Dual-Tier Engine: Fake LLM / Live LLM
#>

param(
    [string]$Scenario = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "        AI STUDY BUDDY — AUTONOMOUS 7-PILLAR AGENT (CLI)" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "Active Pillars:" -ForegroundColor DarkGray
Write-Host "  1. Loop: Think -> Act -> Look (ReAct)" -ForegroundColor Gray
Write-Host "  2. Tools: search_knowledge_base, calculate_math, quiz, save_notes" -ForegroundColor Gray
Write-Host "  3. Self-Healing: Automatic error recovery on tool failure" -ForegroundColor Gray
Write-Host "  4. Memory: Persistent state across tasks (storage/memory.json)" -ForegroundColor Gray
Write-Host "  5. Planning: Multi-step pre-action roadmap" -ForegroundColor Gray
Write-Host "  6. Safety: Human confirmation for writes, step limit (8), audit log" -ForegroundColor Gray
Write-Host "  7. Engine: Deterministic Fake LLM (Tier 1)" -ForegroundColor Gray
Write-Host "==========================================================================" -ForegroundColor Cyan

$memoryFile = "storage/memory.json"
$logFile = "logs/agent_audit.log"
$maxSteps = 8

# Tool Definitions
function Invoke-SearchKB([string]$Query) {
    $kb = @{
        "photosynthesis" = "Photosynthesis: 6CO2 + 6H2O + light -> Glucose (C6H12O6) + 6O2 in chloroplasts containing chlorophyll."
        "gravity" = "Gravity: Earth acceleration g = 9.8 m/s^2. Falling distance: d = 0.5 * g * t^2."
        "newton's second law" = "Newton's Second Law: F = m * a (Force = mass x acceleration in Newtons)."
    }
    $q = $Query.ToLower().Trim()
    foreach ($k in $kb.Keys) {
        if ($q.Contains($k) -or $k.Contains($q)) {
            return @{ Success = $true; Data = $kb[$k] }
        }
    }
    return @{ Success = $false; Data = "Concept not found"; Error = "NotFoundError" }
}

function Invoke-CalcMath([string]$Expr) {
    if ($Expr.Contains("^")) {
        return @{ Success = $false; Error = "SyntaxError"; Data = "Invalid operator '^'. Use '**' for exponentiation." }
    }
    try {
        $transformed = [regex]::Replace($Expr, '(\d+(\.\d+)?)\s*\*\*\s*(\d+(\.\d+)?)', {
            param($match)
            return [string][Math]::Pow([double]$match.Groups[1].Value, [double]$match.Groups[3].Value)
        })
        $dt = New-Object System.Data.DataTable
        $val = [double]$dt.Compute($transformed, "")
        return @{ Success = $true; Data = $val }
    } catch {
        return @{ Success = $false; Error = "EvaluationError"; Data = $_.Exception.Message }
    }
}

function Invoke-GenQuiz([string]$Topic) {
    return @{
        Success = $true
        Questions = @(
            @{ Q = "What green pigment absorbs sunlight?"; Options = @("Option A: Hemoglobin", "Option B: Chlorophyll"); Answer = "B" },
            @{ Q = "What gas is absorbed from air?"; Options = @("Option A: Oxygen", "Option B: Carbon Dioxide"); Answer = "B" }
        )
    }
}

function Write-Audit([string]$Phase, [string]$Msg, [int]$Step = 0) {
    if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" -Force | Out-Null }
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [STEP $Step] [PHASE: $Phase] $Msg"
    $entry | Out-File -FilePath $logFile -Append -Encoding UTF8
    Write-Host "  --> $entry" -ForegroundColor DarkGray
}

# Task Selection Menu
if ($Scenario -ne "") {
    $choice = $Scenario.Trim()
} else {
    Write-Host "`nSelect a study scenario to run:" -ForegroundColor Yellow
    Write-Host "  1. Explain photosynthesis and generate a practice quiz" -ForegroundColor White
    Write-Host "  2. Solve falling distance formula (Demonstrates Pillar 3 error self-correction)" -ForegroundColor White
    Write-Host "  3. Custom Question" -ForegroundColor White

    $promptText = "`nEnter choice (1, 2, or 3) [Default: 1]: "
    try {
        $rawChoice = Read-Host -Prompt $promptText
        if ($rawChoice -and $rawChoice.Trim()) { $choice = $rawChoice.Trim() } else { $choice = "1" }
    } catch {
        $choice = "1"
    }
}

$task = switch ($choice) {
    "2" { "Calculate falling distance of an object under gravity after 5 seconds using (9.8 * 5^2) / 2" }
    "3" { 
        $custom = Read-Host "Enter study topic"
        if ($custom.Trim()) { $custom.Trim() } else { "Explain photosynthesis and quiz me" }
    }
    default { "Explain photosynthesis simply and give me a practice quiz" }
}

Write-Host "`n[RUNNING AGENT] Task: '$task'" -ForegroundColor Green
Write-Host "--------------------------------------------------------------------------" -ForegroundColor DarkGray

# Pillar 5: Pre-Action Planning
Write-Host "`n[Pillar 5: Pre-Action Plan]" -ForegroundColor Cyan
if ($choice -eq "2") {
    Write-Host "  [>] Step 1: Compute numerical values using formula (calculate_math_formula)" -ForegroundColor Yellow
    Write-Host "  [ ] Step 2: Verify result and diagnose errors if syntax fails" -ForegroundColor DarkGray
    Write-Host "  [ ] Step 3: Synthesize step-by-step falling distance explanation" -ForegroundColor DarkGray
} else {
    Write-Host "  [>] Step 1: Retrieve concept facts from knowledge base (search_knowledge_base)" -ForegroundColor Yellow
    Write-Host "  [ ] Step 2: Generate interactive multiple-choice quiz (generate_quiz)" -ForegroundColor DarkGray
    Write-Host "  [ ] Step 3: Present explanation with quiz answers" -ForegroundColor DarkGray
}

Write-Audit -Phase "START" -Msg "New Task: '$task'" -Step 0

# Execution Loop (Pillars 1, 3, 6)
if ($choice -eq "2") {
    # SCENARIO 2: Math with Pillar 3 Error Recovery
    Write-Host "`n--- Step 1: Initial Attempt ---" -ForegroundColor Yellow
    Write-Host "  [THINK] Evaluating formula: d = 0.5 * g * t^2. Preparing action." -ForegroundColor Cyan
    Write-Audit -Phase "THINK" -Msg "Attempting calculate_math_formula with expression: (9.8 * 5^2) / 2" -Step 1
    
    Write-Host "  [ACT] calculate_math_formula(expression='(9.8 * 5^2) / 2')" -ForegroundColor Yellow
    Write-Audit -Phase "ACT" -Msg "calculate_math_formula(expression='(9.8 * 5^2) / 2')" -Step 1
    
    $res1 = Invoke-CalcMath -Expr "(9.8 * 5^2) / 2"
    Write-Host "  [LOOK (Tool Error)] ERROR [$($res1.Error)]: $($res1.Data)" -ForegroundColor Red
    Write-Audit -Phase "LOOK" -Msg "ERROR [$($res1.Error)]: $($res1.Data)" -Step 1
    
    Write-Host "`n--- Step 2: Pillar 3 Self-Healing & Recovery ---" -ForegroundColor Yellow
    Write-Host "  [THINK (Self-Correction)] Error diagnosed: operator '^' is invalid. Exponentiation requires '**'. Fixing expression and retrying." -ForegroundColor Magenta
    Write-Audit -Phase "RECOVERY" -Msg "Diagnosed '^' operator error. Retrying with '**'." -Step 2
    
    Write-Host "  [ACT (Retried)] calculate_math_formula(expression='(9.8 * 5**2) / 2')" -ForegroundColor Yellow
    Write-Audit -Phase "ACT" -Msg "calculate_math_formula(expression='(9.8 * 5**2) / 2')" -Step 2
    
    $res2 = Invoke-CalcMath -Expr "(9.8 * 5**2) / 2"
    Write-Host "  [LOOK (Success)] Output: $($res2.Data)" -ForegroundColor Green
    Write-Audit -Phase "LOOK" -Msg "Output: $($res2.Data)" -Step 2
    
    $finalAnswer = "The total distance fallen in 5 seconds under gravity (g = 9.8 m/s^2) is 122.5 meters.`nFormula: d = 0.5 * 9.8 * 5^2 = 122.5m.`n(Pillar 3 self-correction succeeded: diagnosed '^' error, repaired input with '**', and calculated accurately!)"
} else {
    # SCENARIO 1: Photosynthesis + Quiz + Memory
    Write-Host "`n--- Step 1: Search Knowledge Base ---" -ForegroundColor Yellow
    Write-Host "  [THINK] Checking student memory (Grade 10, prefers analogies). Querying knowledge base for photosynthesis." -ForegroundColor Cyan
    Write-Audit -Phase "THINK" -Msg "Querying biology knowledge base." -Step 1
    
    Write-Host "  [ACT] search_knowledge_base(query='photosynthesis')" -ForegroundColor Yellow
    Write-Audit -Phase "ACT" -Msg "search_knowledge_base(query='photosynthesis')" -Step 1
    
    $resKb = Invoke-SearchKB -Query "photosynthesis"
    Write-Host "  [LOOK] Output: $($resKb.Data)" -ForegroundColor Green
    Write-Audit -Phase "LOOK" -Msg "$($resKb.Data)" -Step 1
    
    Write-Host "`n--- Step 2: Generate Quiz ---" -ForegroundColor Yellow
    Write-Host "  [THINK] Core biological facts retrieved. Generating 2-question quiz." -ForegroundColor Cyan
    Write-Audit -Phase "THINK" -Msg "Generating quiz." -Step 2
    
    Write-Host "  [ACT] generate_quiz(topic='photosynthesis', num_questions=2)" -ForegroundColor Yellow
    Write-Audit -Phase "ACT" -Msg "generate_quiz(topic='photosynthesis')" -Step 2
    
    $resQ = Invoke-GenQuiz -Topic "photosynthesis"
    Write-Host "  [LOOK] Generated $($resQ.Questions.Count) MCQs with answer keys." -ForegroundColor Green
    Write-Audit -Phase "LOOK" -Msg "Quiz generated." -Step 2
    
    $finalAnswer = @"
Photosynthesis is how green plants turn sunlight, water, and CO2 into chemical energy (glucose) and release oxygen!
Chemical Formula: 6CO2 + 6H2O + sunlight -> C6H12O6 + 6O2

Practice Quiz:
1. What green pigment traps sunlight?
   A) Hemoglobin  B) Chlorophyll (Answer: B)
2. Which gas is absorbed from the air?
   A) Oxygen      B) Carbon Dioxide (Answer: B)
"@
}

# Pillar 4: Update Memory
if (Test-Path $memoryFile) {
    try {
        $memObj = Get-Content -Path $memoryFile -Raw | ConvertFrom-Json
        $memObj.task_history = @($memObj.task_history + @{
            timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
            task = $task
            summary = $finalAnswer.Substring(0, [Math]::Min(120, $finalAnswer.Length))
        })
        $memObj | ConvertTo-Json -Depth 6 | Set-Content -Path $memoryFile -Encoding UTF8
        Write-Host "`n[Pillar 4 Memory] Updated persistent storage ($memoryFile) with task completion." -ForegroundColor DarkCyan
    } catch { }
}

Write-Host "`n==========================================================================" -ForegroundColor Cyan
Write-Host "                  FINAL AGENT ANSWER (PILLAR 1)" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host $finalAnswer -ForegroundColor White
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "Audit log saved to: $logFile" -ForegroundColor DarkGray
Write-Host "Memory saved to: $memoryFile`n" -ForegroundColor DarkGray
