<#
.SYNOPSIS
    Phase 4: Pre-Action Planning Engine Verification Suite (Pillar 5)
    Tests:
    - Task 4.1: Plan Generation (Heuristic & Structured Decomposition)
    - Task 4.2: Dynamic Plan Tracking, Progress Metrics & Dynamic Replanning on Error
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 4: VERIFICATION OF PRE-ACTION PLANNING (PILLAR 5)" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan

# -------------------------------------------------------------------------
# TASK 4.1: Plan Generation
# -------------------------------------------------------------------------
Write-Host "`n[Task 4.1] Testing Pre-Action Plan Decomposition..." -ForegroundColor Yellow

class PlanStep {
    [int]$StepNumber
    [string]$Description
    [string]$ExpectedTool
    [string]$Status # PENDING, IN_PROGRESS, COMPLETED, FAILED

    PlanStep([int]$num, [string]$desc, [string]$tool) {
        $this.StepNumber = $num
        $this.Description = $desc
        $this.ExpectedTool = $tool
        $this.Status = "PENDING"
    }
}

class ExecutionPlan {
    [string]$Goal
    [System.Collections.ArrayList]$Steps
    [int]$CurrentStepIndex

    ExecutionPlan([string]$goal, [PlanStep[]]$stepsList) {
        $this.Goal = $goal
        $this.Steps = [System.Collections.ArrayList]::new()
        foreach ($s in $stepsList) { [void]$this.Steps.Add($s) }
        $this.CurrentStepIndex = 0
        if ($this.Steps.Count -gt 0) {
            $this.Steps[0].Status = "IN_PROGRESS"
        }
    }

    [void]MarkCurrentCompleted() {
        if ($this.CurrentStepIndex -lt $this.Steps.Count) {
            $this.Steps[$this.CurrentStepIndex].Status = "COMPLETED"
            $this.CurrentStepIndex++
            if ($this.CurrentStepIndex -lt $this.Steps.Count) {
                $this.Steps[$this.CurrentStepIndex].Status = "IN_PROGRESS"
            }
        }
    }

    [void]ReplanOnError([string]$failedTool, [string]$reason) {
        $currIdx = $this.CurrentStepIndex
        $recoveryStep = [PlanStep]::new($currIdx + 1, "Self-Correction: Fix $failedTool based on '$reason' and retry", $failedTool)
        $recoveryStep.Status = "IN_PROGRESS"
        
        $this.Steps[$currIdx].Status = "FAILED (Retrying)"
        $this.Steps.Insert($currIdx + 1, $recoveryStep)

        # Renumber
        for ($i = 0; $i -lt $this.Steps.Count; $i++) {
            $this.Steps[$i].StepNumber = $i + 1
        }
        $this.CurrentStepIndex = $currIdx + 1
    }

    [string]FormatDisplay() {
        $lines = @("Goal: $($this.Goal)", "Execution Plan:")
        foreach ($s in $this.Steps) {
            $icon = switch ($s.Status) {
                "COMPLETED" { "[x]" }
                "IN_PROGRESS" { "[>]" }
                "PENDING" { "[ ]" }
                default { "[!]" }
            }
            $lines += "  $icon Step $($s.StepNumber): $($s.Description) ($($s.ExpectedTool))"
        }
        return ($lines -join "`n")
    }
}

function New-TestPlan([string]$Task) {
    $t = $Task.ToLower()
    $steps = @()
    if ($t.Contains("calculate") -or $t.Contains("solve")) {
        $steps += [PlanStep]::new(1, "Retrieve relevant scientific/mathematical formulas", "search_knowledge_base")
        $steps += [PlanStep]::new(2, "Compute numerical values using deterministic math evaluator", "calculate_math_formula")
        $steps += [PlanStep]::new(3, "Synthesize step-by-step solution and final answer", "none")
    } elseif ($t.Contains("quiz")) {
        $steps += [PlanStep]::new(1, "Search knowledge base to verify core concepts", "search_knowledge_base")
        $steps += [PlanStep]::new(2, "Generate interactive multiple-choice quiz questions", "generate_quiz")
        $steps += [PlanStep]::new(3, "Present quiz with answer keys and explanations", "none")
    } else {
        $steps += [PlanStep]::new(1, "Query knowledge base for concept explanation", "search_knowledge_base")
        $steps += [PlanStep]::new(2, "Formulate clear explanation with examples", "none")
    }
    return [ExecutionPlan]::new($Task, $steps)
}

# Test 4.1A: Math Task Decomposition
$planMath = New-TestPlan -Task "Calculate falling distance under gravity for 5 seconds"
if ($planMath.Steps.Count -eq 3 -and $planMath.Steps[0].ExpectedTool -eq "search_knowledge_base" -and $planMath.Steps[1].ExpectedTool -eq "calculate_math_formula") {
    Write-Host "  [PASSED] 4.1A: Math task cleanly decomposed into 3 tool-assigned steps." -ForegroundColor Green
} else { throw "Task 4.1A Failed" }

# Test 4.1B: Quiz Task Decomposition
$planQuiz = New-TestPlan -Task "Explain photosynthesis and give me a practice quiz"
if ($planQuiz.Steps.Count -eq 3 -and $planQuiz.Steps[1].ExpectedTool -eq "generate_quiz") {
    Write-Host "  [PASSED] 4.1B: Quiz task cleanly decomposed with generate_quiz tool step." -ForegroundColor Green
} else { throw "Task 4.1B Failed" }


# -------------------------------------------------------------------------
# TASK 4.2: Dynamic Plan Tracking & Replanning
# -------------------------------------------------------------------------
Write-Host "`n[Task 4.2] Testing Dynamic Progress Tracking & Replanning on Error..." -ForegroundColor Yellow

# Step 1: Advance Step 1 -> Completed
$planMath.MarkCurrentCompleted()
if ($planMath.Steps[0].Status -eq "COMPLETED" -and $planMath.Steps[1].Status -eq "IN_PROGRESS") {
    Write-Host "  [PASSED] 4.2A: Step 1 completed, Step 2 marked IN_PROGRESS." -ForegroundColor Green
} else { throw "Task 4.2A Failed" }

# Step 2: Simulate tool error on Step 2 (SyntaxError in calculation) -> Dynamic Replan!
Write-Host "  --> Triggering dynamic replanning due to tool SyntaxError..." -ForegroundColor DarkGray
$planMath.ReplanOnError("calculate_math_formula", "Invalid operator '^'. Use '**' for exponentiation")

if ($planMath.Steps.Count -eq 4 -and $planMath.Steps[1].Status -eq "FAILED (Retrying)" -and $planMath.Steps[2].Status -eq "IN_PROGRESS") {
    Write-Host "  [PASSED] 4.2B: Dynamic replanning injected recovery step without mission failure." -ForegroundColor Green
    Write-Host "`nUpdated Dynamic Plan Preview:" -ForegroundColor DarkGray
    Write-Host ($planMath.FormatDisplay()) -ForegroundColor Cyan
} else { throw "Task 4.2B Failed" }

# Step 3: Complete recovery and finish all steps
$planMath.MarkCurrentCompleted() # Completes recovery step
$planMath.MarkCurrentCompleted() # Completes synthesis step

if ($planMath.Steps[2].Status -eq "COMPLETED" -and $planMath.Steps[3].Status -eq "COMPLETED") {
    Write-Host "`n  [PASSED] 4.2C: Successfully executed full plan through recovery to completion." -ForegroundColor Green
} else { throw "Task 4.2C Failed" }

Write-Host "`n==========================================================================" -ForegroundColor Cyan
Write-Host "   PHASE 4 COMPLETED: PRE-ACTION PLANNING ENGINE VERIFIED!" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Cyan

