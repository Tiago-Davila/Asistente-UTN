# UTN Assistant — Infrastructure README

This directory contains the local Docker Compose configuration for the UTN
institutional assistant.

## Services

| Service    | Purpose                                     | Default port |
|------------|---------------------------------------------|--------------|
| `chromadb` | Persistent ChromaDB vector store            | 8001         |
| `ollama`   | Local Ollama LLM and embedding inference    | 11434        |
| `api`      | FastAPI query and admin service             | 8000         |
| `scraper`  | One-shot scraper worker (run on demand)     | —            |
| `processor`| One-shot index processor worker (on demand) | —            |

## Prerequisites

- Docker Engine 24+
- Docker Compose v2
- (Optional) NVIDIA container toolkit for GPU-accelerated Ollama inference

## Quick start

```bash
# 1. Copy and configure the environment file
cp ../utn-assistant/.env.example ../.env
# Edit ../.env with your settings

# 2. Copy and configure sources
cp ../config/sources.example.yaml sources.yaml
# Edit sources.yaml to list your UTN pages

# 3. Start dependencies
docker compose up -d chromadb ollama

# 4. Pull the LLM model (first run only)
docker compose exec ollama ollama pull llama3

# 5. Start the API
docker compose up -d api

# 6. Run a full index build (scrape + process)
docker compose run --rm --profile workers scraper
docker compose run --rm --profile workers processor
```

## Volumes

| Volume          | Contents                              |
|-----------------|---------------------------------------|
| `chromadb_data` | ChromaDB persistent fragment index    |
| `ollama_models` | Downloaded Ollama model weights       |

## Notes

- The `scraper` and `processor` services use the `workers` profile and are
  not started by default. Trigger them manually for source updates (FR-015).
- The previous usable index is preserved until a new update run completes
  successfully (FR-016, research.md §Index Update Safety).
- All core services run locally; no paid external services are used (FR-022).
