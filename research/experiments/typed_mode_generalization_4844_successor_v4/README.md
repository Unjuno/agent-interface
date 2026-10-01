# Issue #5184 — typed-mode allocation -04

Status: `CONSTRUCTION_PASS_FORMAL_NOT_STARTED`.

This v4 bundle is a new seed-pair replication after allocation -03 was retired due to a parallel formal-seed collision. It does not overwrite, pool, or reinterpret any #5184/#5188/#5189 STOP or raw evidence. The new allocation uses formal seeds 866309294/301332595 and construction-only seeds 59003/59004.

The [plan](PLAN.md) defines H/T/D/C/U, protocol, decision gates, exact Docker Desktop commands and scope. Formal data must not be generated until this bundle is frozen in Git, exact source blobs are verified, and the formal seed pair is rechecked across GitHub Issues, PRs, branches and commits.

Construction ran twice on 59003/59004 in the pinned offline Docker Desktop image; both test invocations passed 1/1. The second run followed a test-strengthening change that asserts the frozen v4 formal seed/allocation constants before substituting construction seeds. The source candidate, tests and independent auditor have not been used with formal data. They are not yet in final source freeze.

The hypothesis remains synthetic classifier-family evidence only. No GUI, cross-app, runtime authority, safety, model quality, latency, human-tempo or product claim is made.
