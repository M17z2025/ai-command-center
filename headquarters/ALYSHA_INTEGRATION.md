# Alysha integration contract

Alysha is the first private authenticated interface to Sigma Headquarters.

## Sigma command center
- portfolio source of truth;
- project registry;
- governance;
- authority and agent definitions;
- development, test and release rules.

## Alysha
- owner-authenticated private interface;
- displays Sigma hierarchy and the registered portfolio;
- may submit owner commands into a future governed Sigma runtime;
- may display private mission/evaluation state once that runtime is commissioned.

Alysha must not become a hidden alternative authority to GitHub.

Issue M17z2025/alisha-ai-platform#1160 owns the first visible slice: owner-only /sigma, hierarchy, master agents and links to every Sigma-managed repository.

Live agent/mission state must come from governed runtime evidence. The UI must not manufacture active-agent counts, mission status, learning events or completion claims.


## Universal Expert Mesh visibility

Alysha's owner-only `/sigma` experience should render the governed mesh from:
- `headquarters/mesh/taxonomy.yaml`;
- `headquarters/mesh/leaders.yaml`;
- `headquarters/mesh/pipeline.yaml`;
- `headquarters/mesh/evolution.yaml`;
- `headquarters/mesh/cognitive-methods.yaml`;
- `headquarters/mesh/thinkers.yaml`.

The interface should allow the owner to inspect:
- permanent leaders and their coverage;
- a leader's child specialists/team policy;
- the knowledge taxonomy;
- which experts were selected for a real mission;
- critic/verifier findings;
- agent/config versions and evaluation status;
- the Thinkers / Paradigm Shifters layer and which cognitive lenses were actually selected for a real mission.

Static governance may be rendered directly from versioned GitHub data. "Active", "working", "learning", "mission running", "completed" and similar runtime states require real private runtime evidence and must never be fabricated by the UI.

Issue #22 defines the mesh. Alysha issue #1160 owns the visible private interface slice.
