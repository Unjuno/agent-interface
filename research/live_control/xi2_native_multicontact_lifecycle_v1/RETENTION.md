# Retention boundary

GitHub retains:

- deterministic pre-measurement `source-freeze.tar.gz` at commit `5d8626c5148e193e19c5ad61e60711f2d8dae7dc`;
- readable `REPORT.md`, scenario summary, frozen-auditor result, independent-verifier result and corruption-control summary;
- `formal-witness.json`, one row per all 28 first outcomes, including each original `result.json` SHA-256, XI2 detail sequences, authority release/rejection result, effect value and terminal-neutral assertions;
- explicit `ORCHESTRATION_INCIDENT.md`, including the limitation that the original wrapper stderr sidecar was overwritten and is not raw-retained.

The complete conversation-local archive `xi2_native_multicontact_lifecycle_v1_complete.tar.gz` is **355,974 bytes**, SHA-256 `12589d9e845b9114dba3d60a96834b8e9da60c2b152d1f52d143580921d7de75`. It contains 485 manifest-bound files: frozen source/construction history, all 28 raw case directories and Xorg/inputtest/XI2 logs, wrapper sidecars, audit, independent verifier and corruption-control tooling/results.

A fresh extraction verified all 485 manifest entries. Running the identical frozen auditor on the extracted source/formal directories and rerunning the independent verifier produced byte-identical PASS outputs.

A smaller local compact archive containing the exact six frozen source files, all 28 original `result.json` files, report/audit/verifier/control and incident record is **23,550 bytes**, SHA-256 `a0a36d54cd3f0b968ef172e36ebfb284e128d35accd313611c5a52518d529182`. The GitHub per-case witness cryptographically binds every original result through its individual SHA-256. No claim is made that GitHub retains the bulk Xorg logs or complete archive bytes.
