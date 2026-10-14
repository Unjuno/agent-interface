# A03 saved-raw soft-transition audit supplement

This is a post-hoc, read-only audit of retained A03 inputs, not a new allocation or a rerun. It preserves the original WSLc report, candidate/audit outputs, package manifest, and STOP history unchanged.

The original report and A03 candidate expose only the latest soft event per cover (sequences 96 and 160), while the report records a cumulative total of three. `reaudit_soft_transitions.py` independently walked the relevant retained ammo rows from `events.jsonl`, using the admitted source value/binding, frozen minimum and age limit, and typed sequence/capture timestamps. It imports neither the candidate nor the guard implementation. It reconstructed the three value transitions at sequences **96, 158, and 160**, matching the report's per-decision counts (1 and 2) and cumulative total (3). Sequence 158 was present in raw input but absent from the original latest-event-only output.

Disposition: `PASS_RAW_SOFT_TRANSITION_RECONSTRUCTION_SCOPED`. This refines the evidence-coverage limitation: the original report still does not list every soft row, but the retained raw stream supports reconstruction of all three rows represented by the two nonzero report counters. It does not change A03's candidate result or claim that its original auditor covered the omitted row. It adds no WSLc behavior, production wiring, live invalidation, task effect, recovery, survival, or product evidence. It does not clear #59's live allocation or #8685's shared-lane ownership gate.

Run the audit without WSLc from the repository root:

```powershell
python -B research/doom/typed_guard_wslc_replay_a03_20261013/audit_supplement/reaudit_soft_transitions.py `
  research/doom/typed_guard_wslc_replay_a03_20261013 `
  research/doom/typed_guard_wslc_replay_a03_20261013/audit_supplement/soft-transition-audit.json
```

The script verifies the original 28-file SHA-256 manifest before reading the raw report and event stream. `soft-transition-audit.json` retains the reconstructed rows and source hashes. `SUPPLEMENT_SHA256SUMS.txt` binds this script, result, and note. The original `SHA256SUMS.txt` remains unchanged and binds only the original A03 package.
