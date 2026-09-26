# Sigma Knowledge & Workforce Infrastructure

## Objective
Turn Sigma from a governed agent registry into a measurable, continuously refreshed expert network running on the owner's private OVH/VPS.

## Architecture

```text
Authoritative / approved web sources
        |
        v
Source Registry -> Fetch/Change Detector -> Normalizer -> Provenance Store
                                            |
                       +--------------------+------------------+
                       |                                       |
                       v                                       v
                 Lexical Index                           Vector Index
                       \                                       /
                        +------ Hybrid Retrieval Gateway ------+
                                         |
                                  Sigma Mission Runtime
                                         |
                  outcomes / gaps / critic / verifier / failures
                                         |
                                         v
                               Capability Gap Detector
                                         |
                                Recruitment Factory
                                         |
                      curriculum + benchmark + deduplication
                                         |
                             Independent Evaluation
                           /           |             \
                      reject       candidate       promote
                                                   |
                                            Workforce Registry
                                                   |
                                        Dashboard / Mesh API
```

## Self-hosted-first components

Initial implementation should avoid paid managed dependencies:
- PostgreSQL + pgvector for durable metadata, provenance, workforce and vector retrieval.
- PostgreSQL full-text search initially; add a dedicated lexical engine only when benchmarks justify it.
- Object storage: existing approved private storage / S3-compatible self-hosted or already-authorised storage.
- Python workers for fetch, parsing, chunking, embeddings, evaluation and scheduling.
- Redis is optional for queue/cache only when workload justifies it; PostgreSQL-backed jobs are acceptable initially.
- Existing Sigma model-provider abstraction; local OpenAI-compatible inference endpoint preferred under owner free/self-hosted-first direction.
- GitHub stores governance definitions and promoted non-secret agent metadata; operational documents, embeddings, prompts, telemetry and private mission state remain private.

## Knowledge Loop
DISCOVER -> SOURCE POLICY -> FETCH -> HASH/CHANGE DETECT -> NORMALIZE -> CHUNK -> CLASSIFY -> INDEX -> VERIFY -> PUBLISH INDEX VERSION -> REFRESH/EXPIRE.

Every indexed chunk requires source URI/identifier, source tier, retrieval date, publication/effective date where available, content hash, licence/usage note, domain tags and correction/removal state.

Freshness is domain-specific. Current law, regulation, markets, APIs and guidance receive short TTLs; stable historical/reference material can have longer TTLs.

## Recruitment Loop
OBSERVE DEMAND -> FIND COVERAGE GAP -> PROPOSE SPECIALIST -> DEDUPLICATE -> DEFINE PARENT/SCOPE -> BUILD CURRICULUM -> BUILD BENCHMARK -> EVALUATE -> ADVERSARIAL TEST -> CERTIFY OR REJECT -> VERSION -> REGISTER -> MONITOR -> RECERTIFY/RETIRE.

Inputs include taxonomy gaps, low-confidence missions, repeated critic findings, failed user journeys, unresolved engineering incidents, new jurisdictions/platforms/industries and owner-requested capability.

Headcount growth is an output, never the optimisation target. A candidate that does not improve benchmark coverage or task outcomes is rejected/merged.

## Core private tables
- sources
- source_versions
- documents
- document_chunks
- knowledge_domains
- chunk_domains
- index_versions
- retrieval_events
- workforce_agents
- agent_capabilities
- agent_versions
- curricula
- benchmarks
- benchmark_runs
- certifications
- mission_assignments
- capability_gaps
- recruitment_candidates
- promotion_decisions
- knowledge_refresh_jobs
- audit_events

## APIs
- GET /workforce/summary
- GET /workforce/agents
- GET /workforce/agents/{id}
- GET /workforce/growth
- GET /knowledge/coverage
- GET /knowledge/freshness
- GET /knowledge/sources
- POST /knowledge/search
- GET /recruitment/queue
- GET /evaluations
- GET /missions/active

## Dashboard headline
Registered | Operational | Certified | Black Belt | Active | Temporary | Added 24h | Retired 24h | Domains | Subjects | Knowledge Freshness | Benchmark Pass Rate.

## Security
- Public internet content is untrusted input, never executable instruction.
- Fetchers have no repository/production credentials.
- Parser/indexer is isolated from mission action tools.
- Prompt/tool injection is stripped/flagged and retained as data, not instruction.
- Source allow/deny policy and rate limits.
- Secrets only from private runtime secret management.
- Private data cannot enter public GitHub knowledge artifacts.
- Every promotion and knowledge correction is auditable and reversible.

## Scale
Phase 1: exact registry compiler + PostgreSQL schema + source registry + hybrid retrieval + dashboard API.
Phase 2: scheduled freshness/change detection + capability gap detector + recruitment candidates.
Phase 3: curriculum/benchmark/evaluation/certification automation.
Phase 4: dashboard visual mesh + growth telemetry + recertification.
Phase 5: scale testing toward 1K/10K/100K/1M definitions only after routing and evaluation benchmarks prove acceptable latency/quality.
