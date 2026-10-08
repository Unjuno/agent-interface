# Issue 5716 host construction plan

Allocation: `5716-TELEMETRY-IDENTIFIABILITY-HOST-CONSTRUCTION-20261001-01`

## H / T / D / C / U

- **H:** Two ground-truth worlds with byte-identical controller-visible telemetry, one where a physical release happened but its event was dropped and one where release did not happen, are indistinguishable to a telemetry-only checker. With release-channel completeness unknown, both must be `UNKNOWN_TELEMETRY`.
- **T:** One Python 3.12.10 host candidate process evaluated two identical incomplete-channel projections plus complete-channel present/absent controls. One separate raw-only auditor checked the four output rows; two post-hoc literal raw audits followed, without a candidate rerun. No candidate retry.
- **D:** Both identical worlds must return exactly `UNKNOWN_TELEMETRY`; complete/present must return `CONFIRMED_COMPLETE`; complete/absent must return `CONFIRMED_OMISSION`. The raw bytes must match the frozen digest and literal fixture. Otherwise FAIL/HOLD.
- **C:** Finite synthetic events, Python 3.12.10 host only. Docker Desktop `desktop-linux` did not answer its read-only version handshake, so this allocation is construction-only and has no container/image identity.
- **U:** Does not establish real telemetry loss, validate an external effect oracle, measure workflow conformance, or infer task correctness, safety, or product behavior.

Test-first note: the naive rule “no release row means confirmed omission” failed before the final classifier was run; it mislabeled both indistinguishable worlds `CONFIRMED_OMISSION`.

## Outcome

The host candidate and independent audits passed the finite expected classifications. Candidate/auditor counts and raw hashes are recorded under `results/identifiability-host-construction-01/`. A Docker experiment and full path integration remain outstanding.
