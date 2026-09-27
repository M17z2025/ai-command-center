# Sigma Self-Learning and Expanding-Memory Adoption Audit

Issue: #53
Date: 2026-09-27
Status: architecture decision / implementation precursor

## Decision

Use **Graphiti** as Sigma's primary durable temporal knowledge-memory engine.

Use **AgentMemoryBench** as the benchmark/evaluation layer that determines whether memory changes improve continual learning, transfer, repair and forgetting behaviour.

Adapt selected **Letta Code** concepts for agent reflection, skills and reviewed self-improvement, but do not make Letta the authority for Sigma governance or production memory promotion.

Keep **Mem0** as an optional future compatibility/personal-memory adapter, not the institutional-memory core.

Do not adopt **Neo4j Agent Memory** as a second overlapping primary memory framework at this stage. Re-evaluate it later if its reasoning-memory abstractions outperform Graphiti + Sigma-native lesson memory in our benchmarks.

## Why Graphiti is the best primary fit

Upstream: https://github.com/getzep/graphiti
Licence: Apache-2.0.

Graphiti directly matches Sigma's hardest memory requirements:
- temporal facts with validity windows;
- facts can be superseded without deleting history;
- episodes preserve provenance back to raw source material;
- incremental ingestion without full rebuilds;
- hybrid retrieval using semantic + keyword + graph traversal;
- prescribed and learned ontology;
- explicit historical queries;
- self-hosting;
- OpenAI-compatible LLM support including Ollama, vLLM and llama.cpp;
- pluggable graph database backends including FalkorDB and Neo4j.

This is a substantially better fit for Sigma institutional memory than flat vector-only memory because Sigma needs to answer:
- what is true now?
- what used to be true?
- why did a decision change?
- which project/version/source produced a fact?
- which repair superseded an older repair?
- which policy applies to which project and period?

### Critical implementation caveat

Graphiti's upstream documentation warns that local/smaller models may produce invalid structured extraction schemas. Sigma must therefore benchmark the exact local model used for ingestion and cannot assume that because the chat runtime works, graph extraction quality is adequate.

The first Graphiti integration must therefore use a bounded ingestion benchmark and structured-output validation before bulk importing Sigma knowledge.

## Graph backend

Preferred first proof backend: **FalkorDB**, self-hosted on the private Sigma network.

Reasons:
- supported directly by Graphiti;
- Docker/self-host friendly;
- avoids introducing a managed cloud dependency;
- appropriate for a bounded proof before committing to a larger Neo4j operational footprint.

Do not expose the graph database publicly. Store data on a private persistent volume and back it up separately from the public Git repository.

## Inference and embeddings

Reuse Sigma's private model gateway/Ollama-compatible endpoint where extraction quality passes benchmark.

Requirements:
- no paid provider fallback without owner approval;
- LLM endpoint private;
- embedding model self-hosted where practical;
- selected LLM must reliably produce Graphiti structured outputs;
- selected embedding model must be version-pinned and recorded in memory metadata.

If the primary local chat model is poor at structured extraction, use a separate local extraction model rather than weakening schema validation.

## Memory architecture

```text
Source / event / mission / document
             |
             v
      Sigma Intake Gate
      - provenance
      - licence/rights
      - classification
      - freshness
      - source hash
             |
             v
          Graphiti
      temporal context graph
      - entities
      - facts
      - validity windows
      - episodes/provenance
      - relationships
             |
       +-----+------+
       |            |
       v            v
Sigma reviewed   Retrieval API
 lessons           |
       |            v
       +------> Sigma Mesh
                    |
                    v
            Runner / Workers
                    |
                    v
               outcomes
                    |
                    v
          postmortem/candidate
                    |
                    v
          independent benchmark
                    |
             +------+------+
             |             |
           PROMOTE        REJECT
```

## Memory classes

Sigma should explicitly separate:

1. **Raw episode memory**
   - source documents;
   - GitHub events;
   - mission transcripts;
   - test evidence;
   - worker evidence.
   - immutable/source-addressable where possible.

2. **Temporal factual memory**
   - entity/fact relationships;
   - validity windows;
   - supersession;
   - provenance links.
   - Graphiti-owned representation.

3. **Reviewed lessons**
   - existing Sigma `lessons` table;
   - initially CANDIDATE;
   - independently evaluated before promotion.

4. **Procedural/skill memory**
   - successful repair procedures;
   - development playbooks;
   - expert skills.
   - versioned, benchmarked and rollback-capable.

5. **Owner/project preferences**
   - isolated private policy/preferences;
   - never used as public training data;
   - scoped to project/owner context.

## Continual-learning evaluation

Upstream: https://github.com/solomoon313/AgentMemoryBench
Licence: MIT.

Use its methodology, and where practical its code, to create a Sigma-specific memory benchmark suite.

Required metrics:
- recall/precision;
- task success rate;
- learning gain;
- stability loss;
- forgetting rate;
- transfer gain;
- repair gain after bad/obsolete memory;
- false-memory rate;
- stale-fact retrieval rate;
- provenance/citation correctness;
- retrieval latency;
- memory growth rate;
- token/context cost.

A memory strategy cannot be promoted merely because it stores more data.

## Letta Code decision

Upstream: https://github.com/letta-ai/letta-code
Licence: Apache-2.0.

Useful concepts:
- memory blocks;
- skill learning;
- reflection/dreaming;
- git-versioned memory state;
- agent-scoped skills;
- long-horizon identity.

Decision: **ADAPT PATTERNS ONLY**.

Reason:
Letta supports agents rewriting memory, prompts, skills and harness behaviour. That is useful research, but Sigma's authority model forbids uncontrolled production self-rewrite.

For Sigma:
- reflection produces CANDIDATE lessons/skills;
- independent evaluator benchmarks them;
- security/regression checks run;
- promotion is separate;
- rollback target remains.

## Mem0 decision

Upstream: https://github.com/mem0ai/mem0
Licence: Apache-2.0.

Strengths:
- mature production-oriented memory API;
- self-hosted server available;
- PostgreSQL/pgvector deployment path;
- strong user/session/agent memory abstractions;
- multi-signal retrieval and temporal reasoning in current generation.

Concerns for Sigma core:
- current README states reported 2026 benchmark results are from the managed platform and include proprietary optimisations unavailable in the OSS SDK;
- newest ADD-only accumulation model is not by itself sufficient for Sigma's explicit correction/supersession governance;
- overlaps with Graphiti once Graphiti supplies hybrid temporal institutional memory.

Decision: **OPTIONAL / LATER** for user/personal-memory compatibility or comparison benchmark. Not primary institutional memory.

## Neo4j Agent Memory decision

Upstream: https://github.com/neo4j-labs/agent-memory
Licence: Apache-2.0.

Strengths:
- explicit short-term, long-term and reasoning-memory framing;
- graph-native;
- local Ollama/vLLM supported through configurable provider adapters;
- can operate with reduced/no LLM extraction modes.

Concerns:
- overlaps heavily with Graphiti;
- introduces another memory framework and Neo4j-specific operational path before we have benchmark evidence that it is superior;
- upstream documentation examples lean toward dedicated Neo4j/Aura deployment, although self-hosting is possible.

Decision: **BENCHMARK CHALLENGER**, not initial primary engine.

## First implementation slice

1. Add a Sigma `KnowledgeMemory` interface independent of Graphiti.
2. Add provenance-first `MemoryEpisode`, `MemoryFact`, `MemoryQuery` and `MemoryResult` schemas.
3. Implement a deterministic in-memory adapter for CI.
4. Implement a Graphiti adapter behind an opt-in configuration flag.
5. Add private FalkorDB + Graphiti service to the Sigma stack.
6. Reuse the private Ollama-compatible endpoint for extraction where benchmark passes.
7. Add ingestion for:
   - promoted Sigma lessons;
   - project status/architecture decisions;
   - runner cycle outcomes;
   - verified defect/root-cause/repair records.
8. Add retrieval before expert execution.
9. Add post-mission candidate-memory extraction.
10. Benchmark Graphiti vs no-memory baseline and optionally Mem0/Neo4j Agent Memory.

## Hard promotion rules

No item becomes trusted memory solely because:
- an LLM generated it;
- it appeared in a chat;
- it was repeated;
- a worker reported it;
- retrieval ranked it highly.

Trusted memory requires appropriate provenance, classification, contradiction handling and evaluation.

Self-learning never grants new authority.

## Initial adoption states

| Candidate | State | Sigma role |
| --- | --- | --- |
| Graphiti | ADOPT / PRIMARY | Temporal institutional knowledge memory |
| AgentMemoryBench | ADOPT / EVALUATION | Continual-memory benchmark and promotion gate |
| Letta Code | ADAPT PATTERNS | Reflection, skills, candidate self-improvement |
| Mem0 | HOLD / BENCHMARK | Optional personal/agent memory adapter |
| Neo4j Agent Memory | HOLD / CHALLENGER | Benchmark against Graphiti later |

## Acceptance criteria before production use

- private self-hosted service runs without public database exposure;
- exact model/embedding versions are recorded;
- ingestion preserves source/provenance;
- superseded facts remain historically queryable;
- source removal/correction propagates;
- no cross-project/private-data leakage;
- backup/restore is tested;
- benchmark improves over no-memory baseline;
- repair mode demonstrates recovery from intentionally bad/stale memory;
- independent security review passes;
- Sigma retrieval never silently treats CANDIDATE lessons as promoted truth.
