# Sigma Universal Expert Mesh

Status: **governed mesh plus executable runtime source**. The YAML files define organisation, routing, evidence and evolution; `sigma_runtime/` executes those definitions. Live model-backed operation still requires a configured runtime model endpoint and private storage host.

## Canonical owner trigger

**ask sigma mesh**

This phrase invokes **Full Mesh mode** in any Sigma-connected conversation or handoff, including a newly started chat. The Mission Router must perform a full leader relevance scan, route relevant experts, select useful Thinker methods, run independent analysis, cross-expert challenge, Independent Critic, Evidence Verifier, bounded repair and final synthesis.

The trigger is portable because the rule is stored in the Sigma master source of truth rather than relying on one conversation's memory. It does not bypass any owner-gated authority or safety boundary.

## Purpose

Sigma uses a governed **Agentic AI Mesh / application-level Mixture of Experts**:

```text
Mitesh — Root Authority
        |
        v
Sigma Governor
        |
        +--> Mission Router
        |      +--> selects one or more domain leaders
        |      +--> assembles a bounded mission team
        |
        +--> Domain Leaders
        |      +--> permanent specialists
        |      +--> temporary specialists created for the mission
        |
        +--> Independent Critic / Red Team
        +--> Evidence Verifier
        +--> Synthesis Director
        +--> Evaluation & Evolution Controller
```

The term "Mixture of Experts" here describes **application-level orchestration of specialist agents**. It does not claim that Sigma changes or exposes the internal MoE routing of any foundation model.

## Design principles

1. **Universal coverage by taxonomy + fallback** — named domains cover the owner's requested knowledge fields; uncovered subjects route to Research Director plus nearest leaders and may produce a provisional specialist definition.
2. **Authority is fixed; expertise is contestable** — the chain of command controls permissions, while evidence-backed disagreement is expected.
3. **No fake human recreation** — Sigma may use documented cognitive methods associated with exceptional thinkers, but does not claim to recreate their minds, identity, personality or intelligence.
4. **Dynamic teams are bounded** — temporary agents have a parent, mission, capability set, prohibited actions, evidence requirements and expiry/review state.
5. **Complex work is multi-expert** — cross-domain work is routed to multiple leaders rather than forced through one generic agent.
6. **Independent criticism is mandatory** — material conclusions pass through a critic/falsifier and evidence verifier before synthesis.
7. **Evolution is versioned** — postmortems can produce candidate improvements, but candidates cannot promote themselves or expand permissions.
8. **Risk changes the workflow** — medical, legal, financial, security, public-policy and other high-impact work requires stronger evidence and applicable human/owner gates.
9. **Public/private separation** — this public repository stores non-secret definitions only. Private mission payloads, owner memory and credentials belong in an approved private runtime/data store.

## Files

- `taxonomy.yaml` — knowledge map and coverage fallback.
- `leaders.yaml` — permanent domain leaders and team-creation policy.
- `pipeline.yaml` — routing, collaboration, critique, verification and synthesis.
- `evidence.yaml` — source quality, freshness, contradiction and uncertainty rules.
- `evolution.yaml` — controlled learning, benchmarking, promotion and rollback.
- `cognitive-methods.yaml` — machine-readable reasoning archetypes based on documented methods, never human impersonation.
- `thinkers.yaml` — the Thinkers / Paradigm Shifters council mapping historical intellectual frameworks to valid Sigma domains and cognitive methods.

## Runtime contract

A future runtime should load these definitions as versioned configuration and produce durable mission evidence:

- mission ID;
- requester/authority;
- selected leaders and specialists;
- source/evidence set;
- disagreements;
- critic findings;
- verification result;
- final synthesis;
- actions requiring owner approval;
- postmortem;
- candidate lessons;
- exact agent/config versions.

Alysha may visualise these records, but it must not invent live status. GitHub remains the public governance source of truth; private runtime state must be backed by real runtime evidence.

Issue: #22


## Executable runtime

The operational implementation lives in `sigma_runtime/` with CLI entrypoint `scripts/sigma_mesh_runtime.py`.

It can route a mission, form bounded specialist teams, invoke parallel experts, run the independent critic and evidence verifier, repair failed work, synthesize the result, persist an audit trail and store postmortem lessons as **CANDIDATE** changes.

See [docs/SIGMA_MESH_RUNTIME.md](../../docs/SIGMA_MESH_RUNTIME.md).
