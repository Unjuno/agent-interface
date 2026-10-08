# Result — dynamic assurance-case finite T0

Allocation: `dynamic-assurance-case-5332-t0-20260930-01`
Issue: [#5332](https://github.com/Unjuno/agent-interface/issues/5332)
Frozen source main: `bdd093f24c626c7ffadaa7ba2a6c8e408814675c`

## H/T/D/C/U outcome

**H:** In this synthetic suite, compositional currentness, coverage, defeater, and independence gates reject seeded unsupported claims better than receipt counting. **PASS, scoped:** the composite policy matched the independent oracle on all 36 rows, supported the clean baseline, and rejected each of the five seeded fault states. Historical baseline graph revision/digest remained unchanged in the negative-successor case. The six corruption controls were all rejected. The independent audit returned `PASS_READONLY`, with zero audit errors and no authority/effect output.

The weaker arms exposed expected unsound supported cases: `FLAT_RECEIPTS` 5/5 fault states; `STATIC_CASE` 3/5; `DYNAMIC_CASE` 2/5; `DEFEATER_AWARE` 1/5; `INDEPENDENCE_AWARE` 1/5; composite 0/5. These counts describe only the seeded cases, not general performance.

**T:** One frozen host-only T0, six scenarios × six policies. Formal runner and independent raw-only auditor each invoked once; no retries or tuning. **C:** Python 3.14.5, Darwin arm64, stdlib only. Docker/OrbStack was not invoked because no named Obstac slot was granted. The source and exact gates are recorded in `FREEZE.json`; raw/audit hashes are in `SHA256SUMS`.

**U:** Synthetic graph/schema logic only. This does not establish real-world effect truth, causal identification, arbitrary argument-link correctness, production safety, or transfer to GUI/code/RAG. The separately gated container rung remains open.

## Reproduction and local CI

From this directory, the frozen formal commands were:

```sh
python3 -B runner.py formal_raw.json
python3 -B audit.py formal_raw.json audit.json
```

Applicable local checks passed after the formal run:

```sh
python3 -B -m pytest -q test_dynamic_assurance_case.py  # 8 passed
python3 -B -m py_compile candidate.py oracle.py runner.py audit.py test_dynamic_assurance_case.py
git diff --check
```

The runner/auditor invocations are the retained experiment. CI checks validate this implementation and are not additional experimental allocations.
