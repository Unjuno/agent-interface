# Issue #6492 T0 result

Disposition: `METHOD_PASS_SCOPED` for the finite synthetic protocol/provenance fixture.

## Executed work

- Host Python 3.11.9; candidate and auditor used separate invocations. No container, WSLc, GPU/CUDA, model, GUI, screenshot, participant, or real effect was used.
- Construction: `python -m unittest discover -s research/analysis/human_return_to_own_work_6492_t0_20261002_v1 -p 'test_*.py' -v` — exit 0, 1/1 test.
- Formal candidate: `python research/analysis/human_return_to_own_work_6492_t0_20261002_v1/candidate.py --fixture research/analysis/human_return_to_own_work_6492_t0_20261002_v1/fixture.json --output research/analysis/human_return_to_own_work_6492_t0_20261002_v1/raw_candidate.json` — exit 0, exactly 18 ordered rows (six synthetic cases × three arms).
- Independent raw audit: `python research/analysis/human_return_to_own_work_6492_t0_20261002_v1/audit.py --fixture research/analysis/human_return_to_own_work_6492_t0_20261002_v1/fixture.json --oracle research/analysis/human_return_to_own_work_6492_t0_20261002_v1/oracle.json --raw research/analysis/human_return_to_own_work_6492_t0_20261002_v1/raw_candidate.json --freeze research/analysis/human_return_to_own_work_6492_t0_20261002_v1/FREEZE.json --output research/analysis/human_return_to_own_work_6492_t0_20261002_v1/audit.json` — separate invocation, exit 0, zero audit errors.
- All six frozen mutations were rejected: swapped task/window, stale cue after external edit, forged agent-authored cue, duplicate save effect, missing offered-cue field, and delayed emergency release.

## Interpretation

The tested representation preserved identical question, answer choices, task facts, interruption priority and state-change warning across arms. Preserved views remained bound to task/window/surface and pre-interruption version; changed state was marked historical with a warning. A stale user cue was withheld, an unused cue remained explicitly optional, and no cue authorized an effect. Emergency release delay was zero. The oracle's correct-return action did not leak into candidate rows.

This validates only a small authored method fixture and its corruption checks. It provides **no evidence** about human resumption accuracy, memory, time, burden, interruption benefit, actual desktop behavior, privacy risk in a real app, or product safety. T1 would need separate participant consent, privacy and accessibility review; this T0 grants none.

Qualification: the synthetic input fixture also contains `pending_step_code` values that duplicate the separately listed oracle's correct-return labels. The candidate implementation neither reads nor emits this field, and the raw auditor confirms those labels are absent from candidate rows; however, the candidate process had access to the field in its input. Therefore this allocation does **not** establish strict candidate/oracle blindness. Treat the PASS as emitted-packet and audit-method validation only; a future T0 needing blinded candidate inputs must remove that redundant field before its own freeze.

The separate #6480 WSLc request was not assigned and was withdrawn; no container was started for either experiment. Its frozen-main mismatch is recorded as a terminal pre-candidate STOP, not as a scientific result and not as a reason to rebook.

## Hashes

- Freeze SHA-256: `5cad97939cb3b4876d0a2c5d5c7ea8be8a110c7b2580e68d6ff8c586f2ff5028`
- Candidate raw SHA-256: `84fa3cfba45e692189a057831532e8a855701ffbedbb879e7db8b9139b00e900`
- Audit JSON SHA-256: `c724ac943f07ba5a8b8ad82e6d6f5df8066b8a6be17fbee1e5df61698a69ad39`
- Main observed at formal-result checkpoint: `e97d21bb6142b3ed0be00744671d3b16f5cde5bb`.

