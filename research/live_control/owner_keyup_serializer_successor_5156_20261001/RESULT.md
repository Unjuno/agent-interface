# T0-SERDE-01 result — joined-release row construction

## Question and scope

**H:** Allocation 04's `TypeError` is caused by a duplicate `event` keyword, and a non-mutating envelope can preserve the owner event while emitting the `joined_release` event required by the frozen raw auditor.

**T:** Reproduce the original Python expression; serialize explicit-up rows with a dedicated helper; validate a complete synthetic stream and corruption controls against the exact frozen auditor and `EXPECTED.json` from Allocation 04. Frozen auditor SHA-256: `97e88c693b7b24e08d75e599c7471d1b109f6d64e6ffdccdd1cf12566775311b`. Expected inventory SHA-256: `59154415de034e0bbc08ec0b5fad8c0c798085babfd6e87077433ab98d99d179`.

## Result

**D: `PASS_SYNTHETIC_SERIALIZER_CONSTRUCTION_ONLY`.** CPython 3.12.10; `python -m unittest -v test_serializer_successor.py` passed 6/6. `py_compile` passed for the helper, tests, and frozen auditor. The tests prove:

- the original `dict(event="joined_release", **row)` fails with duplicate `event`;
- the helper preserves the input row and emits `event="joined_release"` plus `owner_event="owner_key_release_bracket"`;
- the complete synthetic release inventory passes the unchanged frozen auditor;
- omitted release and corrupted caller identity fail audit;
- unrelated owner events are rejected by the helper.

The synthetic values are test fixtures only. No formal experiment or runner was invoked. Allocation 04 raw and STOP evidence remain immutable.

## C / U

No Docker/OrbStack container, X server, X11, XTest, GUI, physical input, model/provider, GPU, or shared execution lane was used. This checks row construction and compatibility with the frozen audit schema only. It does not establish release timing, owner-runtime behavior, key-up delivery, held-input occupancy, task usefulness, safety, MAP01 efficacy, or transfer. The formal allocation remains consumed; another formal run requires a fresh exact coordinator grant.

## Files

- `serializer_successor.py` — pure envelope helper.
- `test_serializer_successor.py` — six offline tests with synthetic records.
- `frozen_auditor.py`, `EXPECTED.json`, `FREEZE.json` — exact-byte references.
- `README.md` — bounded H/T/D/C/U summary.
