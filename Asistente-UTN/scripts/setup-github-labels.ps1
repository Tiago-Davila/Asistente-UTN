<#
.SYNOPSIS
    Crea o actualiza labels de GitHub para el flujo SDD del Asistente UTN.

.DESCRIPTION
    - Usa GitHub CLI (`gh`) autenticado.
    - Crea labels para backend, frontend, fases, user stories, componentes,
      tipos de trabajo y estados.
    - Es idempotente: si una label existe, actualiza color y descripcion.
    - Incluye -DryRun para revisar cambios sin tocar GitHub.

.NOTES
    Requiere: gh CLI autenticado en el repo.

    Uso:
      .\Asistente-UTN\scripts\setup-github-labels.ps1
      .\Asistente-UTN\scripts\setup-github-labels.ps1 -DryRun
      .\Asistente-UTN\scripts\setup-github-labels.ps1 -Repo "owner/repo"
#>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Repo = ""
)

$ErrorActionPreference = "Stop"

function New-LabelDefinition {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Color,
        [Parameter(Mandatory = $true)][string]$Description
    )

    [PSCustomObject]@{
        Name        = $Name
        Color       = $Color.TrimStart("#")
        Description = $Description
    }
}

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

Write-Host "Preparando labels de GitHub..." -ForegroundColor Cyan
if ($Repo.Trim()) {
    Write-Host "Repo: $Repo" -ForegroundColor Gray
}
else {
    Write-Host "Repo: detectado por gh desde el directorio actual" -ForegroundColor Gray
}

$labels = @(
    # Flujo SDD
    New-LabelDefinition "spec-task" "5319E7" "Tarea generada desde specs/*/tasks.md"
    New-LabelDefinition "sdd" "8250DF" "Artefacto o tarea del flujo Spec-Driven Development"
    New-LabelDefinition "blocked" "B60205" "Bloqueada por dependencia, decision pendiente o fuera de alcance actual"

    # Capas / areas tecnicas
    New-LabelDefinition "backend" "1D76DB" "Trabajo de backend Python, API o servicios"
    New-LabelDefinition "frontend" "0E8A16" "Trabajo de frontend o interfaz web"
    New-LabelDefinition "api" "0052CC" "Contratos, DTOs, rutas o manejo de errores de API"
    New-LabelDefinition "scraper" "FBCA04" "Extraccion, robots.txt, parsing o fuentes web"
    New-LabelDefinition "processor" "D4C5F9" "Limpieza de texto, chunking, embeddings o carga de indice"
    New-LabelDefinition "rag" "7057FF" "Recuperacion, prompt, generacion o reglas RAG"
    New-LabelDefinition "vectorstore" "006B75" "ChromaDB, busqueda semantica o persistencia vectorial"
    New-LabelDefinition "infra" "C5DEF5" "Docker Compose, configuracion local o servicios de infraestructura"
    New-LabelDefinition "tests" "BFDADC" "Tests unitarios, integracion, contrato o e2e"
    New-LabelDefinition "e2e" "D93F0B" "Validacion end-to-end segun quickstart"
    New-LabelDefinition "documentation" "0075CA" "Documentacion, specs o guias"
    New-LabelDefinition "architecture" "5319E7" "Decisiones de arquitectura, capas o diseno transversal"

    # Tipos comunes
    New-LabelDefinition "bug" "D73A4A" "Algo no funciona como se espera"
    New-LabelDefinition "enhancement" "A2EEEF" "Mejora o nueva capacidad"
    New-LabelDefinition "chore" "C2E0C6" "Mantenimiento, setup o tareas auxiliares"

    # Prioridades de spec
    New-LabelDefinition "priority:p1" "B60205" "Prioridad alta / MVP"
    New-LabelDefinition "priority:p2" "D93F0B" "Prioridad media"
    New-LabelDefinition "priority:p3" "FBCA04" "Prioridad baja"

    # User stories
    New-LabelDefinition "us1" "D4C5F9" "US1 - Consulta institucional general"
    New-LabelDefinition "us2" "D4C5F9" "US2 - Respuesta honesta ante falta de informacion"
    New-LabelDefinition "us3" "D4C5F9" "US3 - Indicacion de fuente institucional"
    New-LabelDefinition "us4" "D4C5F9" "US4 - Actualizacion del indice institucional"
    New-LabelDefinition "us5" "D4C5F9" "US5 - Disponibilidad y errores claros"
    New-LabelDefinition "us6" "D4C5F9" "US6 - Filtro por area institucional"
    New-LabelDefinition "us7" "D4C5F9" "US7 - Estado del indice institucional"
)

foreach ($phase in 1..10) {
    $labels += New-LabelDefinition "phase-$phase" "EDEDED" "Fase $phase de specs/001-institutional-assistant/tasks.md"
}

if ($DryRun) {
    Write-Host ""
    Write-Host "[DRY-RUN] Labels a crear/actualizar:" -ForegroundColor Magenta
    $labels | Sort-Object Name | Format-Table Name, Color, Description -AutoSize
    Write-Host ""
    Write-Host "Total labels: $($labels.Count)" -ForegroundColor Cyan
    exit 0
}

Write-Host "Obteniendo labels existentes..." -ForegroundColor Cyan
$existingJson = Invoke-Gh @("label", "list", "--limit", "500", "--json", "name")
$existingNames = @()
if ($existingJson) {
    $existingNames = ($existingJson | ConvertFrom-Json) | ForEach-Object { $_.name }
}

$created = 0
$updated = 0

foreach ($label in $labels) {
    $exists = $existingNames -contains $label.Name

    if ($exists) {
        Write-Host "Actualizando $($label.Name)..." -ForegroundColor Yellow
        Invoke-Gh @(
            "label", "edit", $label.Name,
            "--color", $label.Color,
            "--description", $label.Description
        ) | Out-Null
        $updated++
    }
    else {
        Write-Host "Creando $($label.Name)..." -ForegroundColor Green
        Invoke-Gh @(
            "label", "create", $label.Name,
            "--color", $label.Color,
            "--description", $label.Description
        ) | Out-Null
        $created++
    }
}

Write-Host ""
Write-Host "=== Resumen ===" -ForegroundColor Cyan
Write-Host "  Creadas:      $created" -ForegroundColor Green
Write-Host "  Actualizadas: $updated" -ForegroundColor Yellow
Write-Host "  Total:        $($labels.Count)" -ForegroundColor Gray
