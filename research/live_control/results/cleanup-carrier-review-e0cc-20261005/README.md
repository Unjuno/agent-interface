# Cleanup carrier review and narrow integration

Existing #8012 (`95666c514f142b58cebafc1920b86bcd87a0d8be`) retained useful assertions based on an older #7974. This package extracts only its key cleanup assertions onto exact successor `edcf29449d4f700fee8c87dc93f9aef7862bd5af`. It does not carry #8012's obsolete runtime delta or replace its original evidence. The parent already has the dropped-button and no-duplicate-button cases.

## Contract and findings

H: after explicit key UP, terminal cleanup must avoid redundant release of a neutral key; after three dropped explicit UP attempts, it must retry the still-down key and retain its failed explicit receipt. T: copy the exact carrier method into the parent test; run one positive and three runtime mutations. D: baseline passes, each contract-violating mutation is rejected; a surviving mutation reveals a test gap rather than a production defect. C/U: synthetic state and normal local owner threads; no physical X11, application, game, timing, container or model claim.

| Check | Actual result |
| --- | --- |
| Original carrier assertions on exact parent | PASS, 1 method |
| Force redundant terminal UP | FAIL, 3 release attempts instead of 2 |
| Skip cleanup only after a failed explicit receipt | FAIL: cleanup verified=false; final close also raises with keycode 38 down |
| Remove failed explicit receipt from owner.records during cleanup | PASS: surviving mutation exposes a coverage gap |
| Add `assertIn(failed_receipt, owner.records)`, unchanged parent | PASS, 1 method |
| Same receipt-erasure mutation with added assertion | FAIL at the new membership assertion |

The original test only kept a Python reference to the failed receipt and checked its false status. That did not prove the receipt remained in the owner's history. `recommended-cleanup.patch` adds the original 13 lines plus this membership check (14 lines total). It applies to the pinned parent. `extracted-cleanup.patch` retains the unstrengthened extraction.

The strengthened patch is integrated in existing #7958 after merging the pinned parent. Its runtime delta versus that parent remains the existing two-line wheel tracking hunk. The combined V12 suite passed 15/15, including the wheel cases, per-key cleanup, pending-release latch and V15/V13 compositions. These are overlapping regression runs, not independent samples or latency measurements. The 41 selected source/dependency paths differ from the parent only in the owner wheel hunk and this test method. Compile and scoped source whitespace checks pass.

All first results and error chains are retained. In particular, the skip-cleanup mutant first fails the verified assertion, then its `finally` close also raises; the raw log retains both. No formal allocation or shared resource was consumed. Exact public copies replace only private workspace/runtime path prefixes; `publication-provenance.json` binds original and public bytes. Execution receipt hashes refer to original private logs; the publication provenance and manifest identify the public copies.

## Reproduce

With this repository and the pinned Git objects locally available, `python replay.py /path/to/repository /new/output/directory` replays the six ordinary local controls into a new directory. This portable entry point changes only path/runtime setup from the retained original runner and is guarded against import execution. It never fetches, pushes, starts a live X server, or changes the repository. Its portability wrapper was syntax-checked; the recorded execution used the original runner.

For the integrated candidate, from repository root:

```sh
PYTHONPATH=research/live_control:research/doom python -B -m unittest discover -s research/live_control -p 'test_input_owner_v12*.py' -v
```

Separate existing agent `/root/bugbot` reviewed the exact narrow source diff and raw mutation evidence without rerunning it; no material finding. An initial reviewer statement about distinct button coverage was corrected after exact-ref comparison. Technical review is not a quorum vote. No main merge or #8012 branch modification/closure. FINAL-v5 content quorum, exact current-main nonauthor integration, and current protections remain required.
