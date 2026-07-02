<#
.SYNOPSIS
    Crea issues en GitHub a partir de tasks.md del feature activo.

.DESCRIPTION
    - Lee .specify/feature.json para encontrar el feature activo.
    - Lee tasks.md y parsea cada tarea "- [ ] TXXX ...".
    - Determina fase, user story, prioridad, area tecnica y estado bloqueado.
    - Crea/actualiza labels antes de crear issues, salvo que se use -SkipLabelSetup.
    - Evita issues duplicados comparando por ID de tarea y titulo.
    - Usa -DryRun para mostrar que crearia sin tocar GitHub.

.NOTES
    Requiere: gh CLI autenticado.

    Uso:
      .\Asistente-UTN\scripts\tasks-to-issues.ps1 -DryRun
      .\Asistente-UTN\scripts\tasks-to-issues.ps1
      .\Asistente-UTN\scripts\tasks-to-issues.ps1 -Repo "owner/repo"
      .\Asistente-UTN\scripts\tasks-to-issues.ps1 -SkipLabelSetup
#>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$SkipLabelSetup,
    [string]$Repo = "",
    [int]$Limit = 0
)

$ErrorActionPreference = "Stop"
$MarkdownTick = [char]96

function Invoke-Gh {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $repoArgs = @()
    if ($Repo.Trim()) {
        $repoArgs = @("--repo", $Repo.Trim())
    }

    & gh @repoArgs @Arguments
}

function Add-UniqueLabel {
    param(
        [System.Collections.Generic.List[string]]$Labels,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if (-not $Labels.Contains($Label)) {
        $Labels.Add($Label) | Out-Null
    }
}

function Get-TaskAreaLabels {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][int]$PhaseNumber
    )

    $labels = New-Object System.Collections.Generic.List[string]

    $patterns = @{
        "backend"     = "utn-assistant/(api|config|infra|processor|rag|scraper|vectorstore|tests)/|\.py\b|pyproject\.toml|pytest|FastAPI|Pydantic|ChromaDB|Ollama"
        "frontend"    = "utn-assistant/frontend/|\.tsx?\b|React|Vite|TypeScript|frontend"
        "api"         = "utn-assistant/api/|/query|/index|/health|openapi|DTO|router|contract"
        "scraper"     = "utn-assistant/scraper/|scraper|robots|HTML|Playwright|BeautifulSoup|httpx"
        "processor"   = "utn-assistant/processor/|chunk|embedding|text_cleaner|index_loader"
        "rag"         = "utn-assistant/rag/|RAG|prompt|ResponderConsulta|context|refusal|citation"
        "vectorstore" = "utn-assistant/vectorstore/|ChromaDB|vectorstore|PersistentClient|semantic|metadata filter"
        "infra"       = "utn-assistant/infra/|docker|Docker|compose|\.env"
        "tests"       = "utn-assistant/tests/|test_|pytest|failing unit tests|integration tests|contract tests"
        "e2e"         = "utn-assistant/tests/e2e/|quickstart|E2E|end-to-end"
        "documentation" = "specs/|README|\.md`|documentation|quickstart"
        "architecture" = "domain|enums|repository interface|staging|promotion|layer|architecture"
    }

    foreach ($key in $patterns.Keys) {
        if ($Text -match $patterns[$key]) {
            Add-UniqueLabel $labels $key
        }
    }

    if ($labels.Count -eq 0) {
        if ($PhaseNumber -ge 7 -and $PhaseNumber -le 9) {
            Add-UniqueLabel $labels "frontend"
        }
        else {
            Add-UniqueLabel $labels "backend"
        }
    }

    return $labels
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$featureJsonPath = Join-Path $projectRoot ".specify\feature.json"

if (-not (Test-Path -LiteralPath $featureJsonPath)) {
    throw "No se encontro .specify/feature.json en $projectRoot"
}

$featureJson = Get-Content -LiteralPath $featureJsonPath -Raw | ConvertFrom-Json
$featureDir = $featureJson.feature_directory
if (-not $featureDir) {
    throw ".specify/feature.json no contiene feature_directory"
}

$tasksFile = Join-Path $projectRoot (Join-Path $featureDir "tasks.md")
if (-not (Test-Path -LiteralPath $tasksFile)) {
    throw "No se encontro tasks.md en: $tasksFile"
}

Write-Host "Feature: $featureDir" -ForegroundColor Cyan
Write-Host "Tasks:   $tasksFile" -ForegroundColor Cyan

if (-not $SkipLabelSetup) {
    $labelScript = Join-Path $PSScriptRoot "setup-github-labels.ps1"
    if (-not (Test-Path -LiteralPath $labelScript)) {
        throw "No se encontro setup-github-labels.ps1 en $labelScript"
    }

    if ($DryRun) {
        Write-Host "Validando labels en modo dry-run..." -ForegroundColor Cyan
        & $labelScript -DryRun -Repo $Repo
    }
    else {
        Write-Host "Creando/actualizando labels..." -ForegroundColor Cyan
        & $labelScript -Repo $Repo
    }
}

Write-Host "Obteniendo issues existentes..." -ForegroundColor Cyan
$existingIssuesJson = Invoke-Gh @("issue", "list", "--limit", "1000", "--state", "all", "--json", "title")
$existingTitles = @()
if ($existingIssuesJson) {
    $existingTitles = ($existingIssuesJson | ConvertFrom-Json) | ForEach-Object { $_.title }
}
Write-Host "  Issues existentes: $($existingTitles.Count)" -ForegroundColor Gray

Write-Host "Parseando tasks.md..." -ForegroundColor Cyan
$lines = Get-Content -LiteralPath $tasksFile -Encoding UTF8

$currentPhase = ""
$currentPhaseTitle = ""
$currentPhaseNumber = 0
$tasks = @()

foreach ($line in $lines) {
    if ($line -match "^## Phase\s+(\d+)[:\s]+(.+)$") {
        $currentPhaseNumber = [int]$Matches[1]
        $currentPhase = "phase-$currentPhaseNumber"
        $currentPhaseTitle = $Matches[2].Trim()
        continue
    }

    if ($line -match "^- \[ \] (T\d{3})\s+(.+)$") {
        $taskId = $Matches[1]
        $taskContent = $Matches[2].Trim()
        $taskContentClean = $taskContent -replace "^\[P\]\s*", ""
        $taskContentClean = $taskContentClean -replace "^\[US\d+\]\s*", ""

        $labels = New-Object System.Collections.Generic.List[string]
        Add-UniqueLabel $labels "spec-task"
        Add-UniqueLabel $labels "sdd"
        if ($currentPhase) { Add-UniqueLabel $labels $currentPhase }

        if ($taskContent -match "\[US(\d+)\]") {
            $usNumber = [int]$Matches[1]
            Add-UniqueLabel $labels "us$usNumber"
            if ($usNumber -le 5) {
                Add-UniqueLabel $labels "priority:p1"
            }
            elseif ($usNumber -le 7) {
                Add-UniqueLabel $labels "priority:p2"
            }
        }

        if ($taskContent -match "^BLOCKED:| BLOCKED:") {
            Add-UniqueLabel $labels "blocked"
        }

        $areaLabels = Get-TaskAreaLabels -Text $taskContent -PhaseNumber $currentPhaseNumber
        foreach ($areaLabel in $areaLabels) {
            Add-UniqueLabel $labels $areaLabel
        }

        if ($taskContent -match "\bbug\b|\bfix\b") {
            Add-UniqueLabel $labels "bug"
        }
        elseif ($taskContent -match "Create|Implement|Add|Integrate") {
            Add-UniqueLabel $labels "enhancement"
        }
        else {
            Add-UniqueLabel $labels "chore"
        }

        $titleText = $taskContentClean
        $titleText = $titleText -replace "\s*\(depends on .+\)$", ""
        $titleText = $titleText -replace "^BLOCKED:\s*", "BLOCKED: "
        $title = "$taskId $titleText".Trim()
        if ($title.Length -gt 220) {
            $title = $title.Substring(0, 217) + "..."
        }

        $dependencies = ""
        if ($taskContent -match "\(depends on ([^)]+)\)") {
            $dependencies = $Matches[1].Trim()
        }

        $paths = [regex]::Matches($taskContent, '`([^`]+)`') | ForEach-Object { $_.Groups[1].Value }

        $body = @()
        $body += "## Tarea $taskId"
        $body += ""
        $body += ("**Feature**: " + $MarkdownTick + $featureDir + $MarkdownTick)
        $body += ("**Phase**: " + $MarkdownTick + $currentPhase + $MarkdownTick + " - " + $currentPhaseTitle)
        if ($taskContent -match "\[US(\d+)\]") {
            $body += ("**User Story**: " + $MarkdownTick + "US" + $Matches[1] + $MarkdownTick)
        }
        $body += ""
        $body += "### Descripcion"
        $body += ""
        $body += $taskContentClean
        $body += ""
        if ($paths.Count -gt 0) {
            $body += "### Archivos"
            $body += ""
            foreach ($path in $paths) {
                $body += ("- " + $MarkdownTick + $path + $MarkdownTick)
            }
            $body += ""
        }
        if ($dependencies) {
            $body += "### Dependencias"
            $body += ""
            $body += $dependencies
            $body += ""
        }
        $body += "### Labels sugeridas"
        $body += ""
        $body += ($labels -join ", ")
        $body += ""
        $body += "---"
        $body += ""
        $body += ("> Generado desde " + $MarkdownTick + $featureDir + "/tasks.md" + $MarkdownTick)

        $tasks += [PSCustomObject]@{
            Id     = $taskId
            Title  = $title
            Body   = ($body -join "`n")
            Labels = ($labels | Select-Object -Unique)
        }
    }
}

if ($Limit -gt 0) {
    $tasks = $tasks | Select-Object -First $Limit
}

Write-Host "  Tareas encontradas: $($tasks.Count)" -ForegroundColor Gray

$created = 0
$skipped = 0
$failed = 0

foreach ($task in $tasks) {
    $isDuplicate = $false
    foreach ($existingTitle in $existingTitles) {
        if ($existingTitle -eq $task.Title -or $existingTitle -match "^$($task.Id)\b") {
            $isDuplicate = $true
            break
        }
    }

    if ($isDuplicate) {
        Write-Host "  SKIP $($task.Id): ya existe issue" -ForegroundColor Yellow
        $skipped++
        continue
    }

    $labelsArg = $task.Labels -join ","

    if ($DryRun) {
        Write-Host "  [DRY-RUN] $($task.Id): $($task.Title)" -ForegroundColor Magenta
        Write-Host "    Labels: $labelsArg" -ForegroundColor Gray
        $created++
        continue
    }

    Write-Host "  Creando $($task.Id)..." -ForegroundColor Green -NoNewline
    $tempBody = Join-Path $env:TEMP "gh-issue-body-$($task.Id).md"
    $task.Body | Out-File -FilePath $tempBody -Encoding UTF8 -Force

    try {
        $result = Invoke-Gh @(
            "issue", "create",
            "--title", $task.Title,
            "--body-file", $tempBody,
            "--label", $labelsArg
        )
        Write-Host " OK -> $result" -ForegroundColor Green
        $created++
        $existingTitles += $task.Title
    }
    catch {
        Write-Host " ERROR: $_" -ForegroundColor Red
        $failed++
    }
    finally {
        Remove-Item -LiteralPath $tempBody -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "=== Resumen ===" -ForegroundColor Cyan
Write-Host "  Creados:              $created" -ForegroundColor Green
Write-Host "  Saltados duplicados:  $skipped" -ForegroundColor Yellow
Write-Host "  Fallidos:             $failed" -ForegroundColor Red
Write-Host "  Total procesados:     $($tasks.Count)" -ForegroundColor Gray
