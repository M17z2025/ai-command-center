# Sigma Project Team Ownership

Every build/project handled under Sigma has one accountable project team.

## Chat rule

A ChatGPT conversation is a **work surface**, not a separate development organisation. When a chat maps to an existing project, the agent must load:

1. `projects/registry.yaml`;
2. `headquarters/chat-ownership/teams.yaml`;
3. the project repository contract/status where available;
4. the project's Drive blueprint/build pack when relevant.

The mapped Sigma team remains responsible across old chats, new chats, GitHub sessions and Drive documentation.

## Core team composition

Every project team inherits these independent functions in addition to its domain specialists:

- Sigma Governor — portfolio authority routing;
- Sigma Development Planning Director — executable plan/backlog;
- **Sigma Scouter** — open-source/code/free-API reconnaissance;
- Sigma Solution Judge — independent engineering challenge;
- Sigma Security Gatekeeper — independent release security gate;
- Sigma User Tester — real-browser user acceptance;
- Sigma Evidence Verifier — source/evidence discipline.

The canonical Build Steward assignment in `headquarters/chat-ownership/teams.yaml` supplies the persistent continuity owner, core engineering team and project-specific domain specialists.

## Build ownership

The accountable lead:
- keeps the build moving through the Sigma development loop;
- resumes from repository/blueprint evidence rather than chat memory;
- pulls the appropriate specialists for each task;
- uses Sigma Scouter before rebuilding commodity capability from scratch;
- maintains exact next actions and blockers;
- cannot self-certify security or final user acceptance.

## No duplicate-build rule

If two chats refer to the same product, they are two views of the same build. They do not create separate roadmaps, teams, repositories or competing implementations unless the owner explicitly authorises a fork.

## Blueprint rule

Each master project blueprint/build pack must contain a **Sigma Build Team & Ownership** section naming:
- the project/team profile;
- accountable Sigma lead;
- core specialists;
- mandatory independent gates;
- Sigma Scouter's discovery responsibility;
- GitHub/source-of-truth link where one exists;
- the rule that any project chat resolves back to this same team.

The central manifest is authoritative if a Drive document becomes stale.

## Unknown chat/project

If a new project/chat is not mapped, Sigma Chief of Staff temporarily owns routing. The mission is classified, a project identity is created or linked, then the canonical `headquarters/chat-ownership/teams.yaml` registry is updated. Unknown chats must not silently become disconnected development silos.
