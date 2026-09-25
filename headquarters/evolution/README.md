# Sigma agent evolution

Sigma evolution is controlled improvement, not unrestricted self-modification.

work -> result -> independent critic -> test -> postmortem -> lesson extraction -> candidate version -> benchmark -> red-team -> promotion or rejection

## Rules
1. Every promoted agent definition has a version.
2. A candidate cannot certify itself.
3. Benchmarks include regression and safety checks.
4. Permission expansion is reviewed separately from capability improvement.
5. Production, spend and security gates are never inherited merely because an agent scores better.
6. Failed candidates remain auditable.
7. A rollback target exists for promoted definitions.
8. Learning means reviewed durable changes to memory, procedure or agent definition; not hidden self-rewrite.

## Evidence states
REGISTERED, CANDIDATE, EVALUATED, PROMOTED, REJECTED, RUNTIME VERIFIED.

No status is inferred from prose alone.
