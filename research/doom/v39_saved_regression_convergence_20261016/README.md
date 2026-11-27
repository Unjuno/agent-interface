# Saved V39 A11/A12 regression convergence

This converges PR [#8812](https://github.com/Unjuno/agent-interface/pull/8812),
exact head `320d39b6d8f495c78e4863d15a747ce54eed17ed`, onto main
`f71fce5cbfcf184f18dbe944e7416aae0d1b5763` without restoring old runtime source.
Both original directories retain all **48 files with identical Git blobs/bytes**.
`ORIGINAL_PATHS.json` records their path/blob mapping. The original RESEARCH.md
addition is represented by this current entry, rather than replacing the index.

## Saved outcome and present applicability

- A11 remains **FAIL**: the frozen expected counts 15/20 were stale; raw controller
  and pending-drain logs report 16/22. Final-admission/running-guard counts are 9/7.
  All eight stored suite/mode exit receipts are zero, but the harness gate failed.
- A12 remains **PASS in its historical CPU-fixture scope**, with corrected frozen
  counts 16/22/9/7. Each attempt records 108 test executions; 216 across both attempts.
  Neither producer nor any historical suite was rerun for this convergence.
- All 46 legacy checksum entries and 34 pinned Git source blobs/SHA256s match.
  The historical carry-forward check names `57337e95ecbecf7e762c8ec8091472b79e8ad49f`;
  its 34 source pins, 239 changed-path count and no-overlap claim are checked against Git.
- At this convergence base, only **23/34** pinned sources remain byte-identical.
  The 11 changed paths are listed in `RESULT.json`. Historical success does not
  qualify the current controller, release, source-refresh or planner implementations.

The source inventory is the original runner's static import selection, not proof
that all dynamic imports, dependencies, environment effects or real timing were
covered. Original stderr and exit summaries are retained evidence of the recorded
CPU run, not independent observation of a native effect. No Doom, input, GUI, model,
WSLc/container allocation, physical release, task recovery or efficiency is qualified.
#17/#59/#57 remain unresolved in their respective scopes.

## Saved-only verification

From the repository root, with Python 3.13:

```text
python -B research/doom/v39_saved_regression_convergence_20261016/audit_saved.py
python -B -O research/doom/v39_saved_regression_convergence_20261016/audit_saved.py
python -B -m unittest discover -s research/doom/v39_saved_regression_convergence_20261016 -p test_audit_saved.py -v
python -B -O -m unittest discover -s research/doom/v39_saved_regression_convergence_20261016 -p test_audit_saved.py -v
```

The new reader performs explicit checks that remain enabled under `-O`. It imports
no historical producer/candidate. The 11 methods include ten corruption controls
with coherently recomputed checksums: verdict promotion, boolean exit, changed
counts, duplicate/missing identities, mode disagreement, wrong suite module,
source digest, carry inventory/count and failed raw outcome. These test the reader,
not a repeated historical experiment. Initial RED, line-ending/parser and mutation
fixture corrections, expanded RED and final logs remain in this packet.

Original `audit.py` uses assertions (and A11 incorrectly requires PASS); it is
preserved as history, not endorsed as a sufficient optimized-mode verifier.
Original `run_suites.py` rewrites evidence and `verify_main_carry_forward.py` writes
an exclusive record: **do not execute them to regenerate these saved results**.
The old README reproduction blocks remain frozen historical instructions.

For sparse checkouts, materialize the two original evidence directories from the
integrated commit before auditing. Retrieve missing Git objects through the
repository's ordinary read path; missing objects/files are a verification failure,
not permission to rerun the producer. `SHA256SUMS.txt` pins the local packet files;
the auditor additionally checks originals against the immutable PR head.

Next: select a concrete remaining #59/#17 fault or target-lifecycle integration
boundary through the current work map. This packet removes an unintegrated evidence
PR; it does not add a new execution gate or claim the overall cleanup is complete.
