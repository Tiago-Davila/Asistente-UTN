# 🎓 Asistente UTN

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5+-FF6B35?style=for-the-badge&logo=databricks&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=for-the-badge&logo=llvm&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Asistente institucional RAG 100% local para la Universidad Tecnológica Nacional.**  
Responde preguntas sobre información académica, administrativa, bienestar y extensión usando solo fuentes oficiales de la UTN.

[Inicio rápido](#-inicio-rápido) · [Arquitectura](#-arquitectura) · [API](#-api-rest) · [Configuración](#-configuración) · [Docker](#-docker)

</div>

---

## 📋 Tabla de contenidos

- [¿Qué es?](#-qué-es)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Inicio rápido](#-inicio-rápido)
- [Docker](#-docker)
- [API REST](#-api-rest)
- [Configuración](#-configuración)
- [Pipeline de indexación](#-pipeline-de-indexación)
- [Tests](#-tests)
- [Tecnologías](#-tecnologías)

---

## 🤔 ¿Qué es?

El **Asistente UTN** es un sistema RAG (*Retrieval-Augmented Generation*) institucional completamente local que permite a estudiantes, docentes y administrativos consultar información oficial de la UTN en lenguaje natural, en español rioplatense.

El sistema:
1. **Scrapea** páginas web institucionales de la UTN (respetando `robots.txt`)
2. **Procesa y fragmenta** el contenido en chunks semánticos
3. **Indexa** los fragmentos en un vector store local (ChromaDB) con embeddings multilingües
4. **Responde** preguntas usando recuperación semántica + generación local con Ollama

> 🔒 **100% local. Sin servicios externos de pago. Sin historial de conversación. Sin login.**

---

## ✨ Características

| Característica | Detalle |
|---|---|
| 🗣️ **Español rioplatense** | Todas las respuestas en español argentino |
| 🏫 **4 áreas institucionales** | ACADEMICA · ADMINISTRATIVA · BIENESTAR · EXTENSION |
| 🔍 **Búsqueda semántica** | Embeddings `intfloat/multilingual-e5-base` + coseno en ChromaDB |
| 🤖 **LLM local** | Ollama (`llama3` por defecto) — sin API keys externas |
| 🛡️ **Respuesta controlada** | Rehúsa contestar si no hay contexto suficiente |
| 🔄 **Re-indexación segura** | Estrategia staging-and-swap: el índice anterior se preserva ante fallos |
| 🌐 **Scraper robusto** | httpx para páginas estáticas · Playwright para páginas con JS |
| 📊 **Estado del índice** | Endpoint de salud y estado en tiempo real |
| 🐳 **Docker Compose** | Stack completo listo para levantar |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         CONSULTA DE USUARIO                      │
│                          POST /query                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   FastAPI (api/)     │
                    │  Routers + Schemas   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  ResponderConsulta  │
                    │    Service (rag/)   │
                    └──────┬──────┬───────┘
                           │      │
            ┌──────────────▼─┐  ┌─▼──────────────────┐
            │  Embeddings    │  │  ChromaDB            │
            │  Adapter       │  │  (vectorstore/)      │
            │ (processor/)   │  │  Búsqueda semántica  │
            └────────────────┘  └──────────┬───────────┘
                                           │ top-k fragmentos
                                ┌──────────▼───────────┐
                                │  PromptBuilder (rag/) │
                                │  + OllamaClient       │
                                └──────────┬────────────┘
                                           │
                                ┌──────────▼───────────┐
                                │  AssistantAnswer      │
                                │  con fuentes citadas  │
                                └───────────────────────┘

─────────────────────────────── INDEXACIÓN ────────────────────────

 Fuentes YAML ──► Scraper ──► Processor ──► ChromaDB
  (config/)       (scraper/)  (processor/)  (vectorstore/)
                    │              │
              httpx/Playwright  Chunker +
              + robots.txt     Embeddings
```

### Flujo de consulta

```
1. Usuario envía pregunta (POST /query)
2. EmbeddingsAdapter codifica la pregunta
3. ChromaRepository busca top-k fragmentos por similitud coseno
4. Si score < threshold (0.65) → respuesta de rechazo controlada
5. Si hay contexto → PromptBuilder construye el prompt en español
6. OllamaClient genera la respuesta con llama3
7. Se citan las fuentes con URL, título y área
```

### Flujo de indexación

```
1. POST /index/rebuild (o workers Docker)
2. IndexUpdateRun.start() → estado EN_PROCESO
3. Scraper scrapea todas las fuentes activas
4. TextCleaner limpia el HTML
5. Chunker divide en fragmentos (800 chars / 120 overlap)
6. EmbeddingsAdapter codifica todos los chunks en batch
7. IndexManager.stage_batch() → buffer en memoria (NO escribe aún)
8. IndexUpdateRun.complete() → IndexManager.promote()
9. ChromaRepository.upsert_fragments() → índice actualizado
10. En cualquier fallo → abort() → índice anterior intacto
```

---

## 📁 Estructura del proyecto

```
Asistente-UTN/
├── specs/
│   └── 001-institutional-assistant/
│       ├── spec.md              # Especificación funcional completa
│       ├── plan.md              # Plan técnico de implementación
│       ├── research.md          # Decisiones de arquitectura (ADRs)
│       ├── data-model.md        # Modelo de dominio
│       ├── tasks.md             # Tareas T001–T104
│       ├── quickstart.md        # Guía de validación
│       └── contracts/
│           └── openapi.yaml     # Contrato OpenAPI 3.1.0
│
└── utn-assistant/
    ├── api/                     # 🌐 FastAPI: routers, schemas, errores
    │   ├── main.py              # App factory + exception handlers
    │   ├── schemas.py           # DTOs Pydantic v2
    │   ├── dependencies.py      # Wiring de dependencias
    │   ├── errors.py            # Tipos de excepción del dominio
    │   └── routers/
    │       ├── query.py         # POST /query
    │       ├── index.py         # GET|POST|DELETE /index
    │       └── health.py        # GET /health
    │
    ├── config/                  # ⚙️ Configuración
    │   ├── settings.py          # pydantic-settings desde .env
    │   ├── source_loader.py     # Carga sources.yaml
    │   └── sources.example.yaml # Plantilla de fuentes UTN
    │
    ├── rag/                     # 🧠 Núcleo RAG
    │   ├── domain/              # Entidades, enums, reglas de negocio
    │   │   ├── enums.py         # AreaInstitucional, TipoFuente, etc.
    │   │   ├── sources.py       # InstitutionalSource, ExtractedDocument
    │   │   ├── fragments.py     # ContentFragment, SearchResult
    │   │   ├── queries.py       # UserQuery, AssistantAnswer, CitedSource
    │   │   ├── indexing.py      # IndexUpdateRun, IndexStatus
    │   │   └── rules.py         # Reglas puras: umbral, rechazo, citas
    │   ├── prompting.py         # PromptBuilder (español rioplatense)
    │   └── services/
    │       ├── responder_consulta.py   # Flujo de consulta RAG
    │       ├── indexar_contenido.py    # full_rebuild / incremental_update
    │       ├── consultar_estado.py     # Estado del índice
    │       ├── llm_client.py           # OllamaClient (httpx)
    │       └── health.py               # HealthService
    │
    ├── processor/               # 🔧 Procesamiento de texto
    │   ├── text_cleaner.py      # Limpieza HTML (bs4 + lxml)
    │   ├── chunker.py           # Chunking con overlap
    │   ├── embeddings.py        # EmbeddingsAdapter (sentence-transformers)
    │   └── index_loader.py      # Pipeline documento → fragmentos → vectorstore
    │
    ├── scraper/                 # 🕷️ Scraping web
    │   ├── robots.py            # Respeto robots.txt
    │   ├── client.py            # ScraperClient (httpx + delays)
    │   ├── extractor.py         # HtmlExtractor (estático + Playwright)
    │   └── run.py               # Scraper orquestador
    │
    ├── vectorstore/             # 🗄️ Vector store
    │   ├── repository.py        # Interfaz abstracta
    │   ├── chroma_repository.py # Implementación ChromaDB
    │   ├── index_manager.py     # Staging + promote + abort
    │   └── status.py            # build_index_status()
    │
    ├── tests/                   # 🧪 Tests
    │   ├── unit/                # Tests unitarios por módulo
    │   ├── integration/         # Tests de integración con ChromaDB real
    │   ├── contract/            # Validación del contrato OpenAPI
    │   ├── e2e/                 # 7 escenarios end-to-end
    │   └── fixtures/            # HTML + FAQ dataset (30 preguntas)
    │
    ├── infra/                   # 🐳 Infraestructura
    │   ├── docker-compose.yml
    │   └── Dockerfile.api
    │
    ├── pyproject.toml
    └── .env.example
```

---

## 🚀 Inicio rápido

### Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/) v2+
- Al menos **8 GB de RAM** disponible (para Ollama + embeddings)
- ~5 GB de espacio en disco (modelo llama3 ~4.7 GB)

### 1. Clonar y configurar

```bash
git clone https://github.com/tu-usuario/Asistente-UTN.git
cd Asistente-UTN/utn-assistant

# Copiar configuración de entorno
cp .env.example .env

# Copiar y editar fuentes institucionales
cp config/sources.example.yaml infra/sources.yaml
# Editar infra/sources.yaml con las URLs reales de la UTN
```

### 2. Levantar servicios base

```bash
cd infra
docker compose up -d chromadb ollama
```

### 3. Descargar el modelo LLM

```bash
# Esperar ~5 minutos la primera vez (descarga ~4.7 GB)
docker compose exec ollama ollama pull llama3
```

### 4. Levantar la API

```bash
docker compose up -d api
```

### 5. Indexar contenido

```bash
# Scraper: descarga páginas UTN (respeta robots.txt)
docker compose run --rm --profile workers scraper

# Processor: genera embeddings y carga en ChromaDB
docker compose run --rm --profile workers processor
```

### 6. Hacer una consulta

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuáles son los requisitos para rendir libre en la UTN?",
    "area_filter": "ACADEMICA"
  }'
```

### 7. Verificar estado

```bash
curl http://localhost:8000/health
curl http://localhost:8000/index/status
```

---

## 🐳 Docker

### Servicios

| Servicio | Imagen | Puerto | Descripción |
|---|---|---|---|
| `chromadb` | `chromadb/chroma:latest` | `8001→8000` | Vector store persistente |
| `ollama` | `ollama/ollama:latest` | `11434` | Inferencia LLM local |
| `api` | Build local (`Dockerfile.api`) | `8000` | API FastAPI principal |
| `scraper` | Build local | — | Worker one-shot de scraping |
| `processor` | Build local | — | Worker one-shot de indexación |

> ⚠️ `scraper` y `processor` usan el perfil `workers` — se ejecutan con `docker compose run`, no con `up`.

### Comandos útiles

```bash
# Ver logs de la API
docker compose logs -f api

# Reconstruir la imagen después de cambios en el código
docker compose build api

# Parar todos los servicios
docker compose down

# Parar y eliminar volúmenes (borra el índice)
docker compose down -v

# Reconstruir índice completo vía API
curl -X POST http://localhost:8000/index/rebuild \
  -H "Content-Type: application/json" \
  -d '{"mode": "FULL_REBUILD"}'

# Eliminar índice
curl -X DELETE http://localhost:8000/index
```

### GPU (opcional)

Para usar GPU NVIDIA con Ollama, descomentar en `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### Volúmenes persistentes

| Volumen | Contenido |
|---|---|
| `chromadb_data` | Embeddings e índice vectorial |
| `ollama_models` | Pesos descargados del modelo LLM |

---

## 🌐 API REST

Base URL: `http://localhost:8000`

### `POST /query` — Consultar al asistente

```json
// Request
{
  "question": "¿Cómo me inscribo en materias?",
  "area_filter": "ACADEMICA",   // opcional: ACADEMICA | ADMINISTRATIVA | BIENESTAR | EXTENSION
  "max_results": 5              // opcional: 1-10, default 5
}

// Response 200
{
  "answer": "Para inscribirte en materias debés...",
  "context_sufficient": true,
  "sources": [
    {
      "url": "https://www.utn.edu.ar/es/secretaria-academica",
      "title": "Secretaría Académica — UTN Rectorado",
      "area": "ACADEMICA",
      "regional": "Rectorado",
      "department": null
    }
  ],
  "error": null
}

// Response cuando no hay información suficiente
{
  "answer": "No tengo informacion suficiente sobre este tema en las fuentes institucionales disponibles.",
  "context_sufficient": false,
  "sources": [],
  "error": null
}
```

### `GET /index/status` — Estado del índice

```json
{
  "ready": true,
  "document_count": 42,
  "fragment_count": 318,
  "last_successful_update_at": "2024-06-30T15:30:00Z",
  "covered_areas": ["ACADEMICA", "BIENESTAR"],
  "covered_regionales": ["Rectorado", "Regional Buenos Aires"],
  "recent_failures": []
}
```

### `POST /index/rebuild` — Reconstruir índice

```json
// Full rebuild
{ "mode": "FULL_REBUILD" }

// Actualización incremental
{
  "mode": "INCREMENTAL_SELECTED_SOURCES",
  "selected_source_ids": ["utn-rectorado-academica"]
}
```

### `DELETE /index` — Eliminar índice

Vacía la colección ChromaDB. Requiere confirmación implícita vía HTTP DELETE.

### `GET /health` — Salud del sistema

```json
{
  "status": "ok",          // ok | degraded | unavailable
  "chromadb": true,
  "ollama": true,
  "index_ready": true
}
```

### Códigos de error

| Código | HTTP | Descripción |
|---|---|---|
| `INVALID_QUESTION` | 400 | Pregunta vacía, muy larga (+2000 chars) o área inválida |
| `INDEX_NOT_READY` | 503 | El índice no está inicializado |
| `INDEX_EMPTY` | 503 | El índice existe pero no tiene fragmentos |
| `GENERATOR_UNAVAILABLE` | 503 | Ollama no responde |
| `TIMEOUT` | 503 | Generación excedió el timeout (30s) |
| `ADMIN_OPERATION_NOT_ALLOWED` | 403 | Operación administrativa no permitida |
| `UPDATE_REQUEST_INVALID` | 400 | Parámetros de rebuild inválidos |

---

## ⚙️ Configuración

Todas las variables de entorno se cargan desde `.env`. Ver `.env.example` para referencia completa.

### Variables principales

| Variable | Default | Descripción |
|---|---|---|
| `SOURCES_CONFIG_PATH` | `./config/sources.yaml` | Ruta al YAML de fuentes |
| `CHROMADB_PATH` | `./data/chromadb` | Directorio de persistencia ChromaDB |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Endpoint OpenAI-compatible de Ollama |
| `LLM_MODEL` | `llama3` | Modelo de generación |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-base` | Modelo sentence-transformers |
| `RELEVANCE_THRESHOLD` | `0.65` | Umbral de similitud coseno (0–1) |
| `TOP_K` | `5` | Máximo de fragmentos recuperados por consulta |
| `CHUNK_SIZE` | `800` | Tamaño de chunk en caracteres |
| `CHUNK_OVERLAP` | `120` | Overlap entre chunks |
| `REQUEST_DELAY_SECONDS` | `1.0` | Delay entre requests al mismo dominio |
| `SOURCE_FETCH_TIMEOUT_SECONDS` | `10` | Timeout por URL en el scraper |
| `MAX_QUESTION_LENGTH` | `2000` | Máximo de caracteres por pregunta |
| `GENERATION_TIMEOUT_SECONDS` | `30` | Timeout hard para generación LLM |
| `API_HOST` | `0.0.0.0` | Host de binding de la API |
| `API_PORT` | `8000` | Puerto de la API |

### Configuración de fuentes (`sources.yaml`)

```yaml
sources:
  - id: utn-rectorado-academica        # Identificador único (slug)
    url: https://www.utn.edu.ar/es/secretaria-academica
    title_hint: "Secretaría Académica — UTN Rectorado"
    area: ACADEMICA                    # ACADEMICA | ADMINISTRATIVA | BIENESTAR | EXTENSION
    regional: Rectorado
    source_type: WEB
    active: true
    requires_javascript: false         # true solo si la página necesita JS
    crawl_delay_seconds: 1.5           # override del delay global
    exclude_patterns:
      - /noticias/
      - /eventos/
```

---

## 🔄 Pipeline de indexación

```
sources.yaml
     │
     ▼
 Scraper (scraper/)
  ├── RobotsChecker: verifica robots.txt por dominio
  ├── ScraperClient: GET con httpx + delay entre requests
  └── HtmlExtractor: título + TextCleaner.clean()
       └── Playwright solo si requires_javascript: true
     │
     ▼
 ExtractedDocument[]  (URL, título, texto limpio, área, regional)
     │
     ▼
 IndexLoader (processor/)
  ├── Chunker: split en chunks de 800 chars / 120 overlap
  ├── EmbeddingsAdapter: encode batch con multilingual-e5-base
  └── ContentFragment[] con IDs estables (SHA-256 url::chunk_index)
     │
     ▼
 IndexManager (vectorstore/)
  ├── begin_staging(): abre buffer en memoria
  ├── stage_batch(): guarda fragmentos SIN escribir en ChromaDB
  ├── [si todo OK] promote(): flush a ChromaDB.upsert_fragments()
  └── [si falla]   abort(): descarta buffer, índice anterior intacto
     │
     ▼
 ChromaDB (colección: utn_institutional)
  └── embeddings + metadatos (área, regional, URL, título, fecha)
```

**Garantía de seguridad**: Si el scraping o el procesamiento falla en cualquier punto, el índice activo anterior se preserva completamente. Los usuarios siguen pudiendo consultar sin interrupción.

---

## 🧪 Tests

```bash
cd utn-assistant

# Instalar dependencias de desarrollo
pip install -e ".[dev]"
playwright install chromium

# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov --cov-report=html

# Solo unitarios
pytest tests/unit/

# Solo integración
pytest tests/integration/

# Solo contrato OpenAPI
pytest tests/contract/

# Tests E2E (requiere ChromaDB + Ollama corriendo)
pytest tests/e2e/
```

### Cobertura de tests

| Capa | Tipo | Descripción |
|---|---|---|
| Dominio RAG | Unitario | Validaciones de UserQuery, reglas de umbral, citas, state machine de IndexUpdateRun |
| Processor | Unitario | TextCleaner (HTML → texto limpio), Chunker, EmbeddingsAdapter |
| Scraper | Unitario | HtmlExtractor, ScraperClient (errores, redirects) |
| Servicios RAG | Unitario | PromptBuilder, ResponderConsultaService, IndexarContenidoService |
| Vectorstore | Unitario | Búsqueda, ordering, staging |
| Vectorstore | Integración | ChromaDB real: insert/search/filter/delete |
| Processor | Integración | Pipeline completo documento → fragmentos |
| RAG | Integración | Consulta exitosa, rechazo, integridad de citas, filtro por área |
| Indexación | Integración | Re-indexación segura (run fallido preserva índice) |
| API | Integración | Errores de dependencias, estado del índice, timing |
| API | Contrato | Validación contra `contracts/openapi.yaml` |
| Sistema | E2E | 7 escenarios del quickstart |

---

## 🛠️ Tecnologías

| Tecnología | Versión | Rol |
|---|---|---|
| **Python** | 3.11+ | Lenguaje principal |
| **FastAPI** | >=0.111 | Framework REST API |
| **Uvicorn** | >=0.30 | Servidor ASGI |
| **Pydantic v2** | >=2.7 | Validación de datos y DTOs |
| **pydantic-settings** | >=2.3 | Configuración desde .env |
| **httpx** | >=0.27 | Cliente HTTP (scraper + LLM) |
| **BeautifulSoup4 + lxml** | >=4.12 / >=5.2 | Parseo HTML y extracción de texto |
| **Playwright** | >=1.44 | Scraping de páginas con JavaScript |
| **sentence-transformers** | >=3.0 | Embeddings multilingües |
| **ChromaDB** | >=0.5 | Vector store con similitud coseno |
| **Ollama** | latest | Inferencia LLM local (llama3) |
| **PyYAML** | >=6.0.1 | Carga de configuración de fuentes |
| **pytest** | >=8.2 | Framework de tests |
| **Docker Compose** | v2+ | Orquestación de servicios |

---

## 🗺️ Áreas institucionales

| Área | Descripción |
|---|---|
| 🎓 `ACADEMICA` | Inscripciones, calendarios, planes de estudio, regularidades |
| 🏛️ `ADMINISTRATIVA` | Trámites, certificados, legalizaciones, bedelía |
| 💙 `BIENESTAR` | Becas, comedor, salud, deportes, residencias |
| 🌍 `EXTENSION` | Cursos de extensión, vinculación tecnológica, idiomas |

---

## 📐 Decisiones de diseño

- **Sin frontend**: API REST pura, consumible desde cualquier cliente
- **Sin historial**: Cada consulta es stateless e independiente
- **Sin PDFs**: Solo fuentes web (WEB) en v1
- **Sin servicios externos de pago**: 100% local con Ollama + ChromaDB
- **Respuesta de rechazo exacta**: Texto fijo aprobado institucionalmente cuando no hay contexto
- **Umbral configurable**: `RELEVANCE_THRESHOLD=0.65` ajustable sin redeploy
- **Staging-and-swap**: Nunca se actualiza el índice in-place — nueva versión se promueve solo si está completa

---

<div align="center">

Hecho con ❤️ para la comunidad UTN · Argentina 🇦🇷

</div>
