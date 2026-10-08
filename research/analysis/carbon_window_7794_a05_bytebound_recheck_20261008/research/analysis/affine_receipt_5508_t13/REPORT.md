# Issue #5508 T13 — sink duplicate and out-of-order delivery

## Disposition

**PASS for the preregistered five-case toy-sink gate; no production or real external-effect claim.** The matrix was run exactly once after preregistration in OrbStack's network-disabled pinned Python 3.12 container. The independent auditor reconstructed the output from all ten retained SQLite files and returned PASS. Counts: `CONFIRMED_SAME_ATTEMPT=2`, `UNKNOWN=3`, `NOT_STARTED=0`.

## Formal evidence

- Issue preregistration: comment [#5912666023](https://github.com/Unjuno/agent-interface/issues/5508#issuecomment-5912666023), posted before execution.
- Base repository HEAD: `ae727543f47e48bb1686e706b21ed5d9ba1cc31d`.
- Runtime: OrbStack Docker, Linux/ARM64, `--network none`; `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Frozen runner SHA-256: `dba4e6590dd355bf04491cd77c84e3d1eaf5309201179deea514a2bb19f19f4f`.
- Frozen independent auditor SHA-256: `abaca00d8cf7b3e29e2a50cfd8a98f6c00079b6102bae7fd4df5c513af19d8bd`.
- Raw JSONL SHA-256: `96ab9cee8ae16ea0731d8444a8a8c12f5afb506e4efd6ee3cb5d75e812f92629` (`raw/formal/results.jsonl`).
- Auditor output: `{"audit":"PASS","decision":"PASS","errors":[],"independent_counts":{"CONFIRMED_SAME_ATTEMPT":2,"NOT_STARTED":0,"UNKNOWN":3}}`.

| Case | Sink evidence | Recovery |
|---|---|---|
| exact single `d1` | one exact row; target `target-7` | `CONFIRMED_SAME_ATTEMPT` |
| identical duplicate `d1` | second insert suppressed; still one exact row | `CONFIRMED_SAME_ATTEMPT` |
| conflicting payload under `d1` | rejected; original row and target preserved | `UNKNOWN` |
| distinct `d2` | two rows; latest target differs | `UNKNOWN` |
| `d2` then expected `d1` | two rows; final target matches but cardinality is ambiguous | `UNKNOWN` |

The result supports the narrow composed rule in this simulator: an identical duplicate can be safely suppressed by the sink's unique delivery key, whereas conflicting or multiple delivery identities remain uncertain. In particular, a matching final target does not erase evidence of an out-of-order second effect.

## Auditor mutation controls and deviation

The first post-run mutation-control invocation was invalid: the frozen auditor resolves database evidence relative to the result file, while the initial control harness put mutated JSONL in a temporary directory without copying the DBs. All four mutations were consequently rejected because DB reads failed; that did **not** demonstrate the intended mutation sensitivity.

The control harness alone was then repaired to copy the unchanged DB evidence into its temporary audit root. The runner and independent auditor were not edited and the formal matrix was not rerun. With the repaired harness, all four mutations were rejected for the expected evidence reason: missing case, forged confirmation for conflicting payload, erased out-of-order snapshot, and erased duplicate call.

- Preregistered control-harness SHA-256 (pre-run version): `27aa0b3fa3b1bd4e333be23fef4e8ddeb232c301980fe37ee3b90d235e048c7a`.
- Repaired post-run control-harness SHA-256: `f53a13d23182f9c3baf04675a048e6b646713e288f07afacffb9c99ee1b19829`.
- Repaired-control output SHA-256: `ed9b9e58abb5900a0118dd4e4d19a16feb729c8fb201d62ca533e1e693b1c029` (`raw/formal/corruption-controls.json`).
- Result: `all_rejected=true`, four controls; three forged artifacts retained the candidate manifest's PASS bit, yet the independent audit rejected their evidence. The missing-case mutation also changed the reconstructed gate to FAIL.

The mutation-control subcheck therefore has a disclosed post-run harness repair and is weaker than if it had passed unchanged. The preregistered experimental runner, the five-case allocation, and the auditor bytes remained unchanged throughout.

## Scope and limits

SQLite primary-key behavior, event order, and target state are locally authored. This says nothing about a real service/API accepting duplicate requests, authenticated lineage, cross-store atomicity, host power-loss behavior, arbitrary GUI postconditions, or distributed databases. The final-target condition is a toy semantic observation, not an independently queried external system. See [PLAN.md](PLAN.md) for frozen H/T/D/C/U and exact matrix.
