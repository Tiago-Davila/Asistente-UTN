# Validation Report Template — UTN Institutional Assistant

**Feature**: 001-institutional-assistant  
**Version**: 0.1.0  
**Date**: _fill in_  
**Tester**: _fill in_  
**Environment**: Local Docker Compose (ChromaDB + Ollama)  
**Embedding model**: paraphrase-multilingual-mpnet-base-v2  
**LLM model**: _fill in (e.g., llama3)_  

**Traceability**: T104, quickstart.md Scenarios 1–7, SC-001 through SC-008.

---

## Instructions

Run each validation scenario from `quickstart.md` and record results below.
Mark each success criterion PASS or FAIL with brief evidence.

---

## Scenario 1: Health and Empty Index

**quickstart.md**: Scenario 1  
**Tasks**: T096

| Check | Expected | Result | Status |
|-------|----------|--------|--------|
| `GET /health` responds | 200 with chromadb/ollama fields | | |
| chromadb field value | "ok" when available | | |
| ollama field value | "ok" when available | | |
| `GET /index/status` with empty index | `ready: false`, counts 0 | | |
| `POST /query` before index ready | 503 with structured error | | |
| Error message exposes no internals | No Traceback/class names | | |

**Outcome**: PASS / FAIL  
**Notes**: _fill in_

---

## Scenario 2: Full Source Update

**quickstart.md**: Scenario 2  
**Tasks**: T097

| Check | Expected | Result | Status |
|-------|----------|--------|--------|
| `POST /index/rebuild` returns 202 | run_id, status, counts present | | |
| `documents_indexed` reported | integer ≥ 0 | | |
| `documents_failed` reported | integer ≥ 0 | | |
| `fragments_indexed` reported | integer > 0 on success | | |
| Individual URL failures recorded | failures list populated | | |
| Failed URLs don't stop the whole run | run completes despite failures | | |
| `GET /index/status` after update | `ready: true`, counts > 0 | | |
| `covered_areas` populated | at least one area | | |
| `last_successful_update_at` set | ISO datetime present | | |

**Outcome**: PASS / FAIL  
**Notes**: _fill in_

---

## Scenario 3: Successful Query With Citation

**quickstart.md**: Scenario 3  
**Tasks**: T098

| Check | Expected | Result | Status |
|-------|----------|--------|--------|
| `POST /query` returns 200 | status 200 | | |
| `context_sufficient` is true | true | | |
| At least one source URL | sources.length ≥ 1 | | |
| Source URL is institutional | starts with https://utn or similar | | |
| Page title included when available | sources[0].title present | | |
| Answer is in Argentinian Spanish | natural language, no raw HTML | | |
| Response within 5 seconds (SC-004) | elapsed < 5s | | |

**SC-002**: 100% of answers include at least one source URL: PASS / FAIL  
**SC-004**: Response within 5 seconds for ≥95% of normal queries: PASS / FAIL  
**Outcome**: PASS / FAIL  
**Notes**: _fill in_

---

## Scenario 4: Insufficient Context Refusal

**quickstart.md**: Scenario 4  
**Tasks**: T099

| Check | Expected | Result | Status |
|-------|----------|--------|--------|
| Out-of-corpus query returns 200 | not 4xx/5xx | | |
| `context_sufficient` is false | false | | |
| Answer is exact refusal text | "No tengo informacion suficiente..." | | |
| `sources` is empty | [] | | |
| No error field in refusal | error: null or absent | | |

**SC-003**: 100% of insufficient-context questions return approved refusal: PASS / FAIL  
**Outcome**: PASS / FAIL  
**Notes**: _fill in_

---

## Scenario 5: Area Filtering

**quickstart.md**: Scenario 5  
**Tasks**: T100

| Check | Expected | Result | Status |
|-------|----------|--------|--------|
| No-filter query searches full index | sources from multiple areas | | |
| `area: ACADEMICA` filter restricts results | only ACADEMICA sources | | |
| `area: BIENESTAR` filter restricts results | only BIENESTAR sources | | |
| Area with no content returns refusal | exact refusal text | | |
| Invalid area value returns 400 | structured INVALID_AREA error | | |

**Outcome**: PASS / FAIL  
**Notes**: _fill in_

---

## Scenario 6: Failed Update Preservation

**quickstart.md**: Scenario 6  
**Tasks**: T101

| Check | Expected | Result | Status |
|-------|----------|--------|--------|
| Failed rebuild returns FALLIDO status | status: "FALLIDO" | | |
| Failed run not promoted | promoted: false | | |
| Previous index still ready | `GET /index/status` ready: true | | |
| Queries still answer from previous index | context_sufficient: true | | |
| Previous fragment count unchanged | count matches pre-failure count | | |

**SC-006**: A failed update never replaces the last known usable index: PASS / FAIL  
**Outcome**: PASS / FAIL  
**Notes**: _fill in_

---

## Scenario 7: Input and Dependency Errors

**quickstart.md**: Scenario 7  
**Tasks**: T102

| Check | Expected | Result | Status |
|-------|----------|--------|--------|
| Empty question returns 400 | error.code: INVALID_QUESTION | | |
| Question > 2000 chars returns 400 | error.code: INVALID_QUESTION | | |
| Generator unavailable returns 503 | error.code: GENERATOR_UNAVAILABLE | | |
| Index not ready returns 503 | error.code: INDEX_NOT_READY | | |
| No Traceback in error messages | no stack trace text | | |
| No class names in error messages | no "Exception"/"Error" class refs | | |
| All errors in structured envelope | error.code + error.message present | | |

**Outcome**: PASS / FAIL  
**Notes**: _fill in_

---

## Success Criteria Summary

| Criterion | Description | Target | Result | Status |
|-----------|-------------|--------|--------|--------|
| SC-001 | ≥ 90% of FAQ questions return relevant answer with citation | 90% | _/30_ | |
| SC-002 | 100% of answers include at least one source URL | 100% | | |
| SC-003 | 100% of out-of-scope questions return approved refusal | 100% | | |
| SC-004 | ≥ 95% of normal queries respond within 5 seconds | 95% | | |
| SC-005 | Admins complete update without code changes, receive counts | Yes | | |
| SC-006 | Failed update never replaces usable index | 0 failures | | |
| SC-007 | Corpus supports ≥ 50,000 fragments with expected experience | ≥50k | | |
| SC-008 | ≥ 90% of pilot users can identify source link without assistance | 90% | | |

---

## Overall Validation Result

**Result**: PASS / FAIL  
**Date**: _fill in_  
**Signed by**: _fill in_

### Defects Found

| # | Scenario | Description | Severity | Status |
|---|----------|-------------|----------|--------|
| | | | | |

### Notes

_Fill in any additional observations, environment issues, or follow-up items._
