# Owner-queue saved-result auditor mutation check (A01)

## H / T / D / C / U

- **H:** the retained auditor for the merged owner-queue composition result rejects result mutations that falsify its candidate and parent claims or contradict mocked event counts, while accepting the unmodified result.
- **T:** run `python -B mutation_test.py`, which copies the pinned composition evidence into temporary directories and invokes its exact `audit.py` once on the baseline and once per mutation.
- **D:** baseline must exit 0; each of four independently corrupted JSON records must exit nonzero.
- **C:** adversarial mutations cover candidate cancellation adjudication, candidate expiry timestamp ordering, parent false-positive adjudication, and Xlib event count. These exercise the saved-result auditor and do not re-run the owner-loop tests.
- **U:** fake Xlib saved evidence only. This is auditor robustness evidence, not physical release, live control, task usefulness, bounded recovery, or MAP01 completion.

## Result

Baseline passed. All four mutations were rejected. Exact outputs are in `RAW_MUTATION_TEST.txt`; machine-readable decisions are in `results.json`. The parent evidence is `research/doom/results/map01-v39-release-cleanup-owner-queue-composition-v1/` from merged main commit `23290e22615e9f9d4f10b6ab4694429e19757c9a`.
