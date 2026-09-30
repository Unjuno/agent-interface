# Result — erasure-separated parity and authority boundary T1

Allocation: `erasure-separated-parity-5350-t1-20260930-01`
Issue: [#5350](https://github.com/Unjuno/agent-interface/issues/5350)
Frozen source main: `e81cbac968752791678d22a4de3f2d276497d614`

## H/T/D/C/U outcome

**H — PASS, scoped.** Independent audit returned `PASS_READONLY`; all nine cases matched the literal oracle. Reordered complete delivery produced the same bytes. One loss in each independent parity group recovered the full presentation; two source losses in one group remained incomplete. Single and cross-group reconstructions, including recovered critical chunk `c`, remained non-authoritative. Authority was eligible only when all four exact source chunks arrived with current generation and matching criticality metadata; parity loss alone did not prevent that exact-source condition. Mixed generation and criticality mismatch rejected.

No external effect was emitted.

**T/C:** One host-only deterministic XOR run, Python 3.14.5 / Darwin arm64 / stdlib. Runner and raw-only audit each invoked once. No Docker/OrbStack CLI, network, model, GUI/input, or external operation.

**U:** Synthetic byte-level XOR only. `arrival_tick` is ordering metadata, not elapsed time. No rateless-code result, measured latency/bandwidth, real transport behavior, classifier reliability, GUI safety, or production claim.

Raw/audit hashes are in `SHA256SUMS`; exact freeze and scope are in `FREEZE.json` and `PLAN.md`.

## Local CI

```sh
python3 -B -m pytest -q test_model.py  # 6 passed
python3 -B -m py_compile model.py oracle.py runner.py audit.py test_model.py
git diff --check
```
