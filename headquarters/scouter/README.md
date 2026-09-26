# Sigma Scouter

**Agent:** `sigma-scouter`  
**Parent:** Research & Evidence Director  
**Scope:** portfolio-wide open-source and free-API reconnaissance

Sigma Scouter is the single discovery agent responsible for finding reusable software and code that Sigma can legally adapt rather than repeatedly rebuilding commodity capability from zero.

## Non-negotiable rule

Scouter does **not** treat “free tier”, “free credits”, “community trial”, “developer plan”, “up to N requests”, “non-commercial”, or source-available-with-use-restrictions as **free and unlimited**.

For applications and server APIs, the preferred answer is self-hosted open-source code: Sigma controls the runtime, so there is no vendor request/seat/project quota. Our own compute, storage, bandwidth, carrier or payment-rail costs are still real operational costs.

See `policy.yaml` for the machine-readable gate.

## What Scouter searches for

1. Complete self-hosted applications that can replace or accelerate Sigma product modules.
2. Libraries, engines and reference implementations that can be forked and developed further.
3. Self-hosted APIs for AI, search, auth, realtime, documents, OCR, code execution, GIS, automation, security, observability and deployment.
4. Truly unlimited public APIs only where current evidence explicitly proves no request cap and the data terms allow our intended use.
5. Maintained forks when an upstream project becomes proprietary, archived, unsafe or commercially restricted.

## Mandatory evidence per candidate

- upstream repository/project URL;
- exact licence/SPDX and licence family;
- commercial-use and derivative-work rights;
- self-hostability;
- whether any vendor quota remains;
- whether essential advertised features are proprietary/paid;
- maintenance recency;
- security/supply-chain notes;
- what it does;
- Sigma products/capabilities it can accelerate;
- integration approach: use as service, library, fork, reference only, or reject;
- verification date and source evidence.

## Decision states

| State | Meaning |
| --- | --- |
| **ACCEPT** | Current evidence meets the unlimited-free/open admission rule for the stated use. |
| **FORK_CANDIDATE** | Useful open code, but Sigma should extend or isolate it because upstream has feature-gating, copyleft, or other integration obligations. |
| **REVIEW** | Evidence incomplete or ambiguous. It is not approved for adoption yet. |
| **REJECT** | Trial, quota, restricted-use licence, required paid dependency, unsafe/unmaintained upstream, or rights incompatible with the mission. |

## Portfolio lens

Scouter maps discoveries against the Sigma project registry, including:

- AI/agents/voice: Alysha, Humanit, Sigma runtime;
- business systems: Invoiceit, Legalit, Signit, Marketit, Secure DX style workflows;
- mining/geospatial/intelligence: Lycia Zambia and Total Mining Intelligence;
- health/fitness: BodyFit;
- design/creative: Tattooit, Designit, MI7Z web builder;
- platform/infrastructure: hosting, auth, storage, search, monitoring, security, CI/testing and deployment.

## Current high-value foundation set

The seed catalogue in `catalog.yaml` starts with reusable foundations rather than niche demos:

- **Backend/auth:** Supabase, PocketBase, Appwrite, Keycloak.
- **Workflow:** Temporal, Kestra.
- **AI inference/orchestration:** Ollama, llama.cpp, vLLM, LocalAI, Langflow, Haystack.
- **Realtime/voice/video:** LiveKit, Jitsi.
- **Business/marketing:** ERPNext, Dolibarr, listmonk.
- **Documents/OCR:** Paperless-ngx, Tesseract, PaddleOCR, Docling; Documenso is tracked as a fork candidate because its Community Edition is AGPL while upstream also sells enterprise-only features.
- **Search/data:** Qdrant, Milvus, OpenSearch, Valkey, NATS, Kafka.
- **Observability/testing/security:** Prometheus, Grafana, Uptime Kuma, Playwright, k6, Trivy, ZAP.
- **GIS/mining:** QGIS, PostGIS, OSRM, CesiumJS, pygeoapi.
- **Education/dev learning:** Moodle, Jupyter, Piston, Eclipse Theia.
- **Design:** Penpot, Excalidraw.
- **Deployment:** Caddy, Traefik, Dokku, Coolify, Kubernetes, Moby, SeaweedFS.
- **Web search for Scouter:** self-hosted SearXNG.
- **Explicit no-cap public utility:** the Unlicense currency-api mirror is tracked separately and must not be treated as authoritative trading/LBMA data.

## How Sigma should use discoveries

1. **Do not clone blindly.** Compare architecture, licence, security, maintenance and fit.
2. Prefer **permissive libraries/services** for deep proprietary integration.
3. Use copyleft services with a deliberate boundary and comply with source obligations.
4. Fork only when the maintenance burden is justified by time saved.
5. Never copy proprietary enterprise code or bypass a commercial licence. Reimplement missing functionality independently if legally appropriate.
6. Run the normal Sigma engineering tournament, security gate and user testing before calling an adopted component production-ready.

## Runtime

`sigma_runtime/scouter.py` validates catalogue entries against the policy and can query a configured self-hosted SearXNG JSON endpoint to produce **REVIEW** discoveries. Search hits are never auto-approved: licence and unlimited-use evidence must be verified first.

CLI:

```bash
python scripts/sigma_scouter.py validate
python scripts/sigma_scouter.py list --state ACCEPT
python scripts/sigma_scouter.py queries
SIGMA_SCOUTER_SEARCH_URL=http://127.0.0.1:8080 python scripts/sigma_scouter.py search "open source invoicing self hosted"
```

Scouter is a discovery and evidence function. Adoption remains subject to Sigma engineering, legal/licence and security gates.
