# #6691 A02 — independent OrbStack audit of version-mixture T0

## Result

`PASS_AUDIT_ONLY_SCOPED` for the preserved A01 synthetic candidate/raw artifact. The frozen independent auditor ran once in a separate, digest-pinned OrbStack container, exited 0, reported `errors=[]`, and reconstructed both 37-row cases. A02 candidate invocations=0; auditor invocations=1; retries=0.

Primary B=off estimands:

| Case | Pooled A contrast | Common-version standardized contrast |
|---|---:|---:|
| Equal-effect negative control | 5.0 | 5.0 |
| Version-interaction mixture challenge | 3.2 | 5.0 |

Thus the fixture's outcome-relevant, coalition-dependent A-version mixture changes the pooled label-level contrast while the shared-version contrast remains 5.0. In B=on, the equal-effect case is 4.8889 vs 5.0 and the interaction case 2.5556 vs 4.0; these are structural-support diagnostics only because A2×B2 is infeasible. The auditor excluded that cell from common support, retained it as not assigned, and kept the missing attempt and unknown-version rows unresolved. Safety outcomes were counted separately and were not scalarized into task effect.

## H / T / D / C / U

- **H:** Pooling outcome-relevant versions with coalition-dependent proportions can change a named-mechanism contrast relative to a common-version estimand; version-explicit analysis should expose this without altering task-effect/safety truth.
- **T:** Auditor-only replay of immutable A01 raw/candidate outputs in one fresh OrbStack container; A01 candidate was not rerun. A separate immutable input snapshot and its hashes are included here.
- **D:** PASS only if the independent auditor exits 0 with no errors, reproduces the B=off equal-effect control and version-mixture separation, excludes structural-zero support, and keeps missing/unknown records unresolved. These conditions passed.
- **C:** The authored finite table is designed to create the effect; this is not an estimate from real software or users. A fixed, coalition-invariant stochastic-version policy may have a valid pooled policy-level estimand.
- **U:** No evidence that any previous repository experiment is biased; no real implementation equivalence, causal software effect, GUI, model, user, runtime benefit, safety, or product claim. This validates the method discriminator on its synthetic fixture only.

## Provenance and limits

A01's `STOP_AUDITOR_CONTAINER_LAUNCH` remains unchanged. A02's input files are byte-identical to the merged A01 auditor/source outputs, as confirmed by `SHA256SUMS`; only the auditor was invoked. The original A01 candidate output is not elevated beyond the scope of this new independent audit. Requested Docker resource flags are recorded, but effective CPU/memory enforcement was not established.

See `RUN_RECORD.md` for exact image, container identity, arguments, exit and output hash.
