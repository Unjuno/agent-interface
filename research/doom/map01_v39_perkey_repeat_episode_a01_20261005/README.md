# V39 repeated same-key episode construction A01

This bounded CPU construction tests whether repeated episodes of the same key can be joined inside one outer V39 action/step/owner/intent context by the adapter's existing unique `actuation_id`. It is a distinct successor to the earlier per-key schema boundary (which covered a different ledger) and consumer A03 (which accepted one pair only).

`PREREGISTRATION.md` freezes the hypothesis, four-row synthetic fixture, decision gate and scope. `BASE_PAIR.jsonl` preserves the retained A03 fake-display pair unchanged. `INPUT_EVENTS.jsonl` duplicates it with a 1 ms timestamp offset and a second actuation generation. The unchanged A03 consumer is the baseline; `candidate.py` groups by actuation ID, retains both intervals, and refuses ambiguity or overlap. `audit.py` independently rebuilds intervals from raw event rows without importing the candidate. `test_repeat.py` covers the valid two-episode case and four fail-closed mutations.

This tests representation and identity propagation in deterministic retained fake-display data. It is not an execution of the V39 runtime, physical-key occupancy, game/task feedback, threat response, recovery, or MAP01 evidence. The complete H/T/D/C/U and single-run boundary are recorded in `PREREGISTRATION.md`.
