# Sigma Generator Factory — Algorithmic Solution Report

Issue: #103  
Date: 2026-10-01

## Problem

Sigma needs to create many small generators quickly across departments without repeatedly writing one-off code or giving generated tools arbitrary execution authority.

## Constraints / invariants

- no arbitrary code execution;
- no implicit network/secrets/filesystem/production authority;
- deterministic evidence for random operations;
- bounded resource use;
- definitions must be reviewable in Git;
- runtime must fit existing Python/PyYAML control plane;
- new tools must default to non-executable DRAFT state.

## Candidates considered

### A. External generator service wrapper
**Rejected for V1.** Fast to prototype but introduces third-party availability/terms/privacy dependencies and conflicts with the goal of Sigma-owned execution.

### B. Arbitrary generated Python plugins
**Rejected for V1.** Maximum flexibility but turns generator creation into code execution and supply-chain review for every tool.

### C. Sandboxed arbitrary-code plugins
**Deferred.** Safer than B but still requires a robust sandbox, resource controls, dependency policy and a larger attack surface than the current need justifies.

### D. Declarative fixed-operation runtime
**Selected.** A small operation algebra covers the common cases while keeping validation, determinism and authority straightforward.

## Selected V1 operations

- template;
- choice;
- weighted_choice;
- combine;
- synthetic_records.

## Complexity controls

- input lists capped;
- output count capped;
- Cartesian product size checked before materialisation;
- templates capped before and after rendering;
- generator-spec file size capped for standalone validation;
- seeded PRNG used for reproducible choice behaviour.

## Correctness evidence

Unit tests cover:
- registry validity;
- seeded reproducibility;
- invalid weights;
- Cartesian product correctness;
- Cartesian output cap;
- synthetic record sequence/template behaviour;
- missing template input;
- forbidden capabilities;
- unknown operation;
- draft state.

## Rejected future shortcuts

- \`eval\`;
- \`exec\`;
- dynamic import from generator YAML;
- shell commands;
- arbitrary HTTP URL execution;
- environment-variable interpolation for secrets.

## Automated evidence

Tested code head: `49e1fa0318101448dea930318811d75dd0137612`.

- unit tests: SUCCESS;
- control-plane validator: SUCCESS;
- deterministic mesh smoke: SUCCESS.

The implementation was hardened after adversarial review to validate `with_replacement` as a boolean, reject oversized standalone specs before YAML parsing, and distinguish unsupported template syntax from literal braces supplied in input values.

## Current verdict

**SOURCE CANDIDATE — AUTOMATED VERIFICATION GREEN; INDEPENDENT SOLUTION JUDGE PENDING.**

The selected architecture is the strongest bounded V1 candidate under the stated constraints. The implementing path does not self-certify the required independent judge.
