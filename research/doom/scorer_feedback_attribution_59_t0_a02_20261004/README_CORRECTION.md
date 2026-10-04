# Post-run audit correction

The first A02 candidate execution is retained unchanged in `RESULT.json` and `candidate.stdout.txt`. It reports 13 scorer samples, one positive event, and one negative event; its positive event remains `UNRESOLVED` without any actuation intervals.

The frozen v1 audit then failed because it incorrectly hard-coded 18 expected samples. The frozen `RAW.json` and `scorer-samples.jsonl` both contain 13 rows and are byte-hash pinned; this was an audit expectation defect, not a candidate rerun or a changed scientific threshold. The initial failed audit traceback is preserved in `AUDIT_v1_failed.txt`. Audit v2 compares the raw embedded arrays to their serialized files and derives the sample count from both; it passes without rerunning the candidate. The original `FREEZE.json`, `audit.py`, and `README.md` remain unchanged to retain the first version. The initial README's “18 serialized samples” sentence is superseded by this correction.
