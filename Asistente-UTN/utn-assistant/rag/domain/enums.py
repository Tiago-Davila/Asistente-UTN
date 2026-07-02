"""
rag/domain/enums.py — Closed-value domain enumerations.

All institutional areas, source types, indexing states, and update modes
are defined here as Python enums.  No other module may introduce string
literals for these concepts (constitution §Closed values).

Traceability:
  AreaInstitucional  → FR-009, FR-010, spec §Institutional Areas, data-model.md
  TipoFuente         → spec §Source Types, data-model.md §TipoFuente
  EstadoIndexacion   → data-model.md §EstadoIndexacion, FR-016
  ModoActualizacion  → FR-015, data-model.md §IndexUpdateRun
"""
from __future__ import annotations

from enum import Enum


class AreaInstitucional(str, Enum):
    """Supported institutional areas for source classification and query filtering.

    Using str-Enum so values serialise cleanly to JSON / YAML without extra
    conversion steps.

    Spec §Institutional Areas: ACADEMICA, ADMINISTRATIVA, BIENESTAR, EXTENSION.
    """

    ACADEMICA = "ACADEMICA"
    ADMINISTRATIVA = "ADMINISTRATIVA"
    BIENESTAR = "BIENESTAR"
    EXTENSION = "EXTENSION"


class TipoFuente(str, Enum):
    """Source ingestion type.

    Only WEB is active for the initial version.
    PDF and MANUAL are reserved; active sources must not use them until a later
    spec amendment enables those ingestion paths.

    Spec §Source Types.
    """

    WEB = "WEB"
    PDF = "PDF"      # reserved — not supported in v1 ingestion
    MANUAL = "MANUAL"  # reserved — not supported in v1 ingestion


class EstadoIndexacion(str, Enum):
    """Lifecycle state for an index update run or a document/fragment.

    State machine (data-model.md §EstadoIndexacion):
        PENDIENTE → EN_PROCESO → COMPLETADO  (successful path)
        PENDIENTE → EN_PROCESO → FALLIDO     (failure path)

    Only COMPLETADO runs may promote their fragments to the active index.
    FALLIDO runs preserve the previous usable index (FR-016).
    """

    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"


class ModoActualizacion(str, Enum):
    """Mode for an administrator-triggered index update run.

    FULL_REBUILD               — re-index all configured active sources.
    INCREMENTAL_SELECTED_SOURCES — re-index only the administrator-selected
                                   subset of configured sources (FR-015).
    """

    FULL_REBUILD = "FULL_REBUILD"
    INCREMENTAL_SELECTED_SOURCES = "INCREMENTAL_SELECTED_SOURCES"
