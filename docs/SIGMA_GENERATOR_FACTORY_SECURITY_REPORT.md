# Sigma Generator Factory — Cybersecurity Review Report

Issue: #103  
Date: 2026-10-01  
Review state: IMPLEMENTER SECURITY REVIEW COMPLETE; INDEPENDENT GATE PENDING

## Trust boundaries

Inputs considered untrusted:
- generator YAML definitions;
- CLI JSON inputs;
- draft metadata;
- random-choice lists and weighted objects;
- templates and synthetic field specifications.

Trusted code boundary:
- the fixed \`sigma_runtime.generator_factory\` implementation;
- repository-reviewed policy and registry.

## Controls implemented

- fixed allow-list of operation types;
- unknown operations fail validation;
- capabilities list must be empty in V1;
- explicit forbidden capability list includes network, shell, subprocess, eval, exec, dynamic import, secrets, credential access, arbitrary filesystem, production write and external service;
- only APPROVED + currently valid definitions execute;
- DRAFT/DISABLED cannot execute;
- bounded input/output sizes;
- bounded template/render sizes;
- seeded PRNG for reproducible evidence;
- no environment-variable reads in generator execution;
- no subprocess/network/dynamic-import modules in generator execution;
- draft file write only occurs through an explicit CLI output path.

## Threats considered

### Arbitrary code injection
Mitigation: definitions contain no executable expression language. Placeholder rendering accepts field identifiers only.

### Resource exhaustion
Mitigation: list, output and template size caps; Cartesian size checked before full result creation; standalone draft size is checked before YAML parsing.

### Authority escalation
Mitigation: generator specs do not carry agent permissions and V1 capabilities must be empty.

### Secret exfiltration
Mitigation: runtime has no secret/environment/network operation.

### Supply-chain expansion
Mitigation: V1 adds no dependency beyond existing PyYAML.

### External service terms/privacy
Mitigation: Perchance and other external generator sites are not runtime dependencies and are not automatically called.

## Open assurance items

- exact-head automated CI/test/control-plane result: SUCCESS on tested code head `49e1fa0318101448dea930318811d75dd0137612`;
- independent Sigma Solution Judge review;
- independent Sigma Security Gatekeeper verdict.

## Gate verdict

**BLOCKED / NOT VERIFIED for final merge/release until the independent security gate is completed.**

This status does not mean the source is known unsafe. It means the implementing path cannot self-certify the independent security assurance required by Sigma governance.
