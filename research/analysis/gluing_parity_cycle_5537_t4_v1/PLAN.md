# Issue #5537 T4 — pairwise-compatible parity cycle

## H / T / D / C / U

**H.** Three local contexts can each be internally consistent and pairwise-compatible on every shared variable while admitting no single global assignment. A global-section checker should classify that cycle `NO_GLOBAL_SECTION`; a pairwise-only policy would accept it. A coherent equality control should yield two sections, and an incomplete cover must remain `UNKNOWN`.

**T.** Enumerate the full eight binary assignments over `x,y,z` for three context relations: `x=y`, `y=z`, and `z!=x`. All pairwise variable projections are `{0,1}`, but the three constraints cannot be satisfied simultaneously. Controls: change the last relation to `z=x` (two global sections) and omit that context (incomplete cover). Independently re-enumerate with a separately represented reference checker and reject false certificate, dropped-case, and duplicate-case mutations. No GUI/model/provider/network/task effect.

**D.** Scoped PASS iff the contradictory cycle is pairwise-compatible with zero global sections and no irreversible admission; coherent control has exactly two global sections; incomplete cover is `UNKNOWN` and cannot authorize irreversible action; independent checker agrees on all three cases and all mutation controls are rejected. Any false certificate is FAIL; evidence/schema divergence is STOP.

**C.** Tiny binary finite cover and hand-authored restriction relations; the exact enumeration is complete only for this declared three-variable domain. It tests a higher-order obstruction distinct from direct pairwise contradictory claims, not the truth of any real interface observation.

**U.** No general sheaf/cohomology algorithm, tolerance, freshness, authority override, live GUI, performance, or production correctness claim. T0-T3 issue results remain unchanged.

## Freeze and execution

- Base: `10f94d57fb91f3c656aeb16f81c693a9e70deb26`.
- Freeze time: `2026-09-30T14:59:48Z`.
- Candidate SHA-256: `a474c96b2b950e91ac8e32a1246ca21bd5a31bb6f84e7263304d5360136f8a6f`.
- Independent auditor SHA-256: `b27bf3175dcc6eabd16abc07cd5bb3addb804c3095c8a76ae1f54972a4ba4a3b`.
- Freeze commit: recorded in the PR body and execution report after this source-only commit is created; no candidate/auditor edits are permitted afterward.
- Planned image: already-present `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`; network disabled, read-only root/source, only raw output mount writable, 1 CPU, 256 MiB, 64 pids, all capabilities dropped, no-new-privileges.
- Commands: one `python /src/experiment.py` invocation; only if exit 0, one independent `python /src/audit.py` invocation.
- Shared resource: do not invoke until #5156's exact exclusive slot has ended and its owner/coordinator explicitly releases it. No launch is covered by the #5156 lease.
- After formal invocation, no candidate/auditor edits, reruns, replacements, tuning, or raw rewriting. A failed gate is retained verbatim.
