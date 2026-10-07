# Issue #5313 A01 — retained-receipt boundary localization

## Outcome

`PASS_BOUNDARY_BLAME_REAL_RECEIPT_SCOPED`. The one-shot candidate read eight frozen retained cases without replaying their native processes; the separate raw-only audit passed 48 checks with no errors. Two local-deadline supplements localized the observed blocked operation to the app-server client's diagnostic stderr read, while both remained `blame=UNLOCALIZED` and `SAFE_YIELD`. The two retained-stderr records without a read-entry deadline remained `BLOCKED_DIAGNOSTIC_READ_OBSERVED`, not deadline-breach claims. Healthy and fully closed controls were `blame=NONE`; unsafe component blame count was zero.

This supports mechanism localization in this exact saved receipt family, not fault attribution. The saved records are from a prior controlled synthetic-child native construction, the deadline observation occurs after the deadline, and this experiment did not establish a governing contract that bounds diagnostic collection. It therefore does not establish a violation, successful repair, latency improvement, production frequency, model/backend fault, GUI behavior, or task effect.

## H/T/D/C/U and execution

The preregistered H/T/D/C/U and exact source, receipt-manifest, code, and base identities are in `PROTOCOL.md` and `FREEZE.json`. Input receipts and the historical source snapshot were read-only. Candidate and independent auditor each ran exactly once after freeze; raw outputs are retained under `results/`. Formal native/model replays: 0.

Pre-formal local checks: 13/13 candidate/auditor/mutation tests passed, Python compilation passed, and `git diff --check` passed. The repository's full analysis CI was not run in this intentionally sparse checkout; `check_index.py` was also not considered an applicable standalone complete-index check before this report was indexed. OrbStack was unavailable for this task: image inspection failed with a containerd blob `operation not supported`; no container repair, pull, build, restart, or prune was attempted. This is explicitly a saved-data host analysis, not a container result.

## Immutable execution outputs

- `results/candidate.raw.json` SHA-256: `ab3ea920aac088be34ebb6283ca8668e94af439d1305206b8676c74259fc25e7`
- `results/audit.json` SHA-256: `e47895df85213633de799f91aa6dd75c4407aa618b8f07b9b0e66abae6e56fd4`
- Audit: 8 cases, 48 checks, `PASS`, 0 errors, 2 scoped deadline/read localizations, 0 unsafe component blames.

Historical Issue #5313 T0 and its existing PR/result were not modified. This is an additive successor package; the source receipt package remains byte-for-byte unchanged.
