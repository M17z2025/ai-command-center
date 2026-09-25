# Sigma Universal Expert Mesh

Status: **control-plane definition**. These files define the organisation, routing, evidence and evolution contracts for Sigma's expert mesh. They do not by themselves prove that an autonomous multi-agent runtime is running.

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
