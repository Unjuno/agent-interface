# Audit v2: typed evidence and actual payload identity

This is the controlling correction to the evidence-gate coverage described in
the original REPORT.md, prompted by PR review 5398441445 and inline comments
4171212319 / 4171212332. Every original v1 package file remains byte-identical
to head b8fb01e8fb851c48ef8a83a02c1c39a7fca50352. The original source, frozen
cases, all raw rows, first failures, execution receipts and original SHA256SUMS
are unchanged. This directory adds an independently frozen ordinary raw-only
audit revision; no producer/runtime/candidate/implementation-mutant is rerun.

The v1 oracle compared terminal/effect values using Python equality and did not
bind the recorded execute sequence to the frozen input. The four reported
copied-row changes all reproduced v1 errors=[] / mismatch_count=0. V2 uses
recursive exact JSON type/value identity and literal ordered trace/journal
references. It binds core-result trace to the recorded admission, execute's
typed sequence to independently specified input, effect/observation references,
and final terminal/journal fields. The retained v1 raw-only oracle continues to
classify semantic admission differences; v2 adds evidence identity checks.

| Fixed ordinary check | First outcome |
|---|---|
| Existing baseline raw re-audit | 3,072 rows; 2,164 semantic mismatches retained; zero identity errors; exit 0 |
| Existing combined raw re-audit | 3,072 rows; zero mismatches/identity errors; exit 0 |
| Four reported changes against v1 | All four incorrectly accepted, reproduced without producer execution |
| Sixteen directed copied-raw changes against v2 | All sixteen refused; one changed-row identity error each; exit 0 |

Baseline retains 135 actual inert execute entries/completions, including the
previously reported 133 outside the declared valid-input gate. Combined retains
the same two valid completions. Raw SHA-256 remains baseline
4f277eb70ee44af906bdf29330e8728f4ac4863228a4e1cbb5f576b5fbc59392 and combined
d0d369c30bf6f924bb203a8dd731a5519d8bc0c225f81ffdce737d32c4a90807.

The prospective PLAN.md/FREEZE.json was written at 02:03:40.713835 UTC before
checks. Actual UTC operations 02:04:03.522224–02:04:11.927052, one CPU thread,
CPython 3.11.9 on Windows. The 207,737-byte controls record stays below the
256-KiB bound. Original and changed row witnesses, excluded-row binding hashes,
full changed-copy hashes, commands, UTCs, environment overrides and full stdout/
stderr hashes are retained. Every first v2 audit/control/verification command
exited 0.

From the package directory:

```text
python -B audit_v2/auditor.py --arm baseline --raw evidence/baseline.jsonl
python -B audit_v2/auditor.py --arm combined --raw evidence/combined.jsonl
```

controls.py has already saved its first result and refuses to overwrite it.
To reproduce ordinary copied-data controls, export the package into a fresh
private directory and remove only that fresh copy's controls-result.json before
invocation. That operation does not execute the matrix producer. Verification
of the retained outcome requires only audit_v2/verify.py.

This repairs the declared synthetic evidence identity gate. It does not prove
arbitrary hostile log authenticity, exception-message wording, physical clocks,
release/effects, concurrent behavior, public adapters, models or performance.
The original runtime guard behavior and its scope remain unchanged. Original
fourteen controls and v1 engineering failures stay retained; sixteen new raw
controls do not retroactively replace them. Content review must bind to the new
head/digest; the v1 correction objection is retained until explicitly addressed.
Nonauthor current-tree verification and actual application gates remain separate.
