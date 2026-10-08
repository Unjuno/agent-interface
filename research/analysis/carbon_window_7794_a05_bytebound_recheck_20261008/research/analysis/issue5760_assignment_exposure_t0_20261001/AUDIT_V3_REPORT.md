# Issue #5760 — posthoc raw-output audit v3

## H / T / D / C / U

- **H:** The frozen synthetic selection-reversal fixture differs from its assignment-level result when analysis conditions on local execution; a raw-only audit can independently recover the assignment denominator and detect destructive mutations.
- **T:** Read the immutable four-row selection and null fixtures, original candidate/oracle outputs, v1 failure, and v2 STOP receipt. Reconstruct exact rational metrics without invoking the candidate or oracle. Reject: dropping fallback rows, relabeling fallback as local, and zeroing fallback cost.
- **D:** Construction suite: 7/7 passed before the formal audit. Formal audit v3: one invocation, exit 0, `PASS_AUDIT_V3_REPAIR_SCOPED`, zero errors; both raw reconstructions equal frozen values and candidate/oracle output projections; all three mutations rejected. Candidate/oracle invocation counts for v3: zero.
- **C:** Synthetic deterministic fixtures only; no random assignment, live route, application, model, GPU, or human observations. No causal inference or evidence about repository benchmarks.
- **U:** No claim about deployed route effects, Issue #57/#59, user tempo, runtime integration, or product readiness. v1 `FAIL_T0_CONTRACT` and v2 `STOP_AUDIT_V2_CONFIGURATION_MISMATCH` remain unchanged; v3 is a separately frozen audit correction, not a rewrite of those outcomes.

## Reproduction and retained files

Run from this directory:

```powershell
python -B -m unittest -v test_audit_v3
python -B audit_v3.py fixtures.json candidate.stdout.json oracle.stdout.json audit.stdout.json audit_v2.stdout.txt FREEZE_AUDIT_V3.json
```

`FREEZE_AUDIT_V3.json` pins audit/test source hashes, all raw input hashes, allocation IDs, and invocation limits. `AUDIT_V3_EXECUTION.json` retains exit status and call counts; `audit_v3.stdout.json` retains the one-line raw result. `SHA256SUMS` inventories the additive evidence. Earlier raw files and v1/v2 audit evidence were not altered.
