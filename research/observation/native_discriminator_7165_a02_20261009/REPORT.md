# #7165 A02 — first result: HOLD

**Disposition:** `HOLD_AUDITOR_RUNTIME_ERROR`. The frozen candidate completed
once with exit 0 and emitted 2,304 rows. The frozen auditor ran once and exited
1 before writing an audit result: its first mutation control omitted the `fresh`
field, while the control path attempted to call the oracle on that field. This
is a harness failure, not a scientific PASS or FAIL. The pre-registered gate
required the original auditor to complete, so the formal result remains HOLD.

## Saved-raw review

A separately versioned, read-only auditor (`saved_review/auditor_v2.py`) was
applied once to the already-saved raw. It independently reconstructed 2,304 of
2,304 unique states, found no route or decision mismatches against the
always-fresh oracle, and detected all seven synthetic mutation controls. Its
status is `PASS_RAW_RECONSTRUCTION_V2`; it does not repair or replace the
original formal auditor outcome.

Across the enumerated state space, the candidate selected the targeted path in
2 cases and full fresh fallback in 2,302. Those counts describe the constructed
finite grid, not event probabilities. The decisions were A: 256, B: 256, and
UNKNOWN: 1,792. The targeted cases were the only complete, source-valid,
current-generation, current-read cases where both cues agreed. Thus this model
offers no demonstrated memory-specific observation reduction; A01's measured
fresh-cue tie remains the relevant cost observation.

## Scope and next decision

This finite contract fixture supports only the observation that the authored
gate routes incomplete, stale, wrong-source, missing, or contradictory cases
to full fresh revalidation, and that its saved rows agree with the declared
oracle. It assumes source/generation labels are truthful and that values do not
change inside an unchanged generation. It does not test native GUI invalidation,
arbitrary source forgery, asynchronous changes, observation bytes, model cost,
task effects, or user benefit. The first formal outcome stays HOLD; no formal
retry is permitted under this allocation. Any follow-up needs a new, explicit
allocation and should first correct the audit control during construction.

## Reproduction and evidence

- Freeze: `FREEZE.json`; candidate/auditor source commit `7d773a5bd68ec198d5c65c764afb21ebc8553161`.
- Candidate: `python3 candidate.py`; receipt and raw under `runs/candidate/`.
- Original auditor: `python3 auditor.py`; its receipt and traceback are retained under `runs/auditor/`.
- Saved review only: `python3 saved_review/auditor_v2.py`; output under `saved_review/`.
- The six construction tests passed before freeze. No native GUI, container, model, or network was used.
- `MANIFEST.json` records hashes for frozen source and retained outputs.
