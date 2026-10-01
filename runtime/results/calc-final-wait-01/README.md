# Primary Calc final-wait comparison: four rows, adoption HOLD

Issue #3700 asked whether a caller-selected 250 ms final wait could avoid an
extra observation compared with 50 ms. The primary assistant used the same
public CLI, full-metadata/inline-PNG host route and fresh Docker Calc environment
for four fixed rows, in 50/250/250/50 order. Input gaps were 20 ms. The frozen
source was `55427ecda1474b43d8a58bbc5714de7285cc8390`; later main changes were not
silently substituted. No production wait default was changed.

| Row | Final wait | Task | Extra observations | Saved result | CLI roundtrip ms |
|---|---:|---|---:|---|---:|
| 1 | 50 ms | 11 × 13 | 1 | 143, correct | 3259.255 |
| 2 | 250 ms | 11 × 13 | 0 | 143, correct | 1481.503 |
| 3 | 250 ms | 17 × 19 | 0 | 323, correct | 1417.038 |
| 4 | 50 ms | 17 × 19 | 1 | 323, correct | 1585.137 |

All initial PNGs are byte-identical: blank A1, the same nonmodal first-run
information banner and no blocking dialog. Row 1's immediate image showed
partial editing; row 4 showed Saving/intermediate editing. The primary withheld
completion and used the one permitted read-only observation in each. Rows 2/3
showed completed values in the immediate image. Completion declarations preceded
independent saved-FODS parsing; the formula and operands/results matched in all
four documents. All four input-release records verify no held keys/buttons.
No input was replayed. All containers exited 0. Captured process-member paths
were absent after forced cleanup; graceful Calc shutdown/full descendant auditing
are not claimed.

**Disposition: HOLD_PRODUCTION_ADOPTION.** Two paired tasks provide a descriptive
observation-count signal, not a reliable latency/cost advantage or a general
250 ms recipe. Exact provider build/reasoning configuration was not exposed.
The same active primary Astra task was used without helper models, but that does
not establish the exact model-identity gate requested by #3700. Host image-render
and separate receipt timestamps, actual token usage and costs are unavailable.
CLI roundtrip and runtime durations are not model-useful feedback latency.
The first row was notably slower despite its shorter final wait; cache, order,
context and scheduling effects remain. No held-out validation was performed.
No complete preregistered-study PASS or human-tempo claim follows.

The plan, all four requests and owner code were frozen before row 1; the
[prerun issue record](https://github.com/Unjuno/agent-interface/issues/3700#issuecomment-5753062289)
includes their freeze hash and the missing endpoints. The
[result record](https://github.com/Unjuno/agent-interface/issues/3700#issuecomment-5753092587)
keeps the issue open. Private harness leases were minted in the execution clock
after each explicit primary decision; this is test authority, not server-issued
freshness or a generally available lease mechanism.

## Retained bundle and read-only verification

`evidence.zip` contains all four local row directories, complete stdout/PNG/raw
reports, requests, programs, declarations, timings, documents, cleanup/terminal
records, plan/freeze/results, the exact exported source closure and its hashes.
It also retains the earlier construction export STOP separately. That first
preparation referenced a nonexistent namespace-package `runtime/__init__.py`;
export failed and the following container exited before any GUI/input. It is
not a formal comparison row. The successful observe-only construction is
described in the issue; its complete output is not bundled here.

Run from any directory with Python standard library only:

```sh
python runtime/results/calc-final-wait-01/verify.py
```

The verifier reads archive members without extracting or importing archived code.
It checks all 258 member hashes, the published freeze, exported source hashes,
response/raw/PNG consistency, frozen requested programs (except the declared
private lease timestamp), fixed waits, stored timing arithmetic, independent
saved values/formula, recorded declarations, observation counts and recorded
cleanup/terminal states. It does not independently prove what the model saw,
the moment of rendering, declaration ordering, live termination or comparative
performance. Archived `run/verify.py` is historical local analysis, not the
portable verifier to run.

Image used: `sha256:41c3190256bf644c8e251bb84d615d2753fae067e347422fd6d3e74ec8d60183`.
Runtime: `/usr/bin/python3`, isolated Xvfb/Openbox/LibreOffice gen, 1024×768 PNG,
network disabled, root/source read-only, 1 GiB memory, 512 MiB private tmpfs.
The image itself is not distributed by this record. See `manifest.json` for
archive/member digests and `RESULT.json` for unrounded recorded intervals.
