# A02 frozen plan — measurement consumer pin repair

## H / T / D / C / U

**H.** Once the A01 source pin is corrected in a fresh, separately versioned
candidate, the same retained V12 down/up measurement pair can be consumed as a
conservative per-key sample-bracket interval without changing event semantics,
input authority or application-effect status.

**T.** Use the byte-identical two-row `INPUT_EVENTS.jsonl` copied from main's
retained fake-display bridge A01. A01's sole invocation stopped on an incorrect
hash literal before producing a candidate; do not repeat that run. Freeze this
A02 candidate, independent auditor, input hash and one-shot output path. Run the
candidate once, then reconstruct the raw independently and apply in-memory
negative controls for actuation identity, brackets, timestamps, authority,
release classification and auditor-visible output corruption.

**D.** PASS only for one joined confirmed down/up pair with exact matching
program, step, owner, intent, key and actuation; identical adapter/source
brackets; ordered exact integer times; no authority/effect claim; candidate
output equal to a separately implemented raw-only audit; all mutation tests
must fail closed. A pin mismatch or missing evidence is STOP. Semantic mismatch
is FAIL.

**C.** This is replay of a previous fake-display construction stream, not a
new physical measurement. It only validates event consumption and conservative
sample-bracketing arithmetic. No game, application or useful effect is observed.

**U.** One F8 pair. No distribution, exact physical occupancy, live threat,
recovery, causal latency, safety-rate or MAP01 progress result.

## Frozen identities

- Current main: `109cedcf1fafc150e235c91141eb47bbc7396b43`.
- Input blob: `eacb735634d6c6761ba7fa39448e6d7d43e342d5`.
- Input SHA-256: `ad0b1c29da4b6269be27e8716cdabfbb25ac49dcf0abd4dba4bd2f7a9f84e4e`.
- A01 STOP: `research/doom/map01_v39_perkey_measurement_consumer_a01_20261005/results/a01/STOP.json`.
- A02 candidate invocation: exactly once, `python3 run.py` from this directory.
- Audit invocation: `python3 audit.py`; frozen output is `results/a02/`.
- No OS input, GUI, game, model/provider, or container is permitted or needed.
