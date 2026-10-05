# Independent technical check of PR #8006

The existing V39 controller/wait/cleanup tests that the author could not import now pass with already-installed Pillow: **39/39** at exact PR #8006 head `66ba74f69d1373399811f62ad950743caad770ed`. A separate reviewer-written probe exercises the exact main-loop AST through renewal rejection, coverless waiting and the post-turn terminal gate: **4/4 scripted schedules pass**. This supports the local soft-stale renewal repair; it is not a FINAL-v5 approval vote, main merge, or live recovery result.

| Check | Result | Actual scope |
|---|---|---|
| New focused tests | 4 pass | Author's helper and extracted wait/submit tests |
| Existing controller tests | 8 pass | Real module imports plus source/helper/branch checks |
| Existing wait/admission tests | 15 pass | Extracted production wait and admission paths |
| Existing failure-cleanup tests | 12 pass | Synthetic cleanup, bounded blocking/error fixtures |
| Reviewer main-loop probe | 4 schedules pass | Exact AST loop, fake queue/future/executor/planner/monitor |

The old test named `test_soft_observation_stale_submit_is_recorded_without_aborting_controller` exercises **initial** cover admission, so it does not substitute for the new renewal-to-coverless loop probe. No unrelated full suite was run. Python 3.12.14, Pillow 12.3.0, NumPy 2.3.5, macOS 27.0.1 arm64; no installs. The 24 pinned source/test/dependency files totaled 267,045 bytes. Source hashes matched before and after execution.

## What the four schedules establish

Soft observation/renewal rejection followed by normal completion preserves the original terminal object and sole admitted cover ID, records the rejected renewal, sends no cancel for it, and makes no planner-interrupt request. Hard or unknown synthetic monitor events while coverless each make exactly one interrupt request and retain the prior terminal; no new admitted renewal or fabricated terminal appears. An unexpected executor rejection raises RuntimeError instead of entering coverless continuation.

The phrase `one finite interrupt` in the original probe output describes a finite scripted call count. `old empty release retained` means an existing synthetic receipt with `verified=true` and empty lists survives the path. The probe **does not** execute a real thread, provider, input owner, controller CLI, model, game or GUI, and does not prove actual cancellation/release timing, physical release, task effect, survival or bounded live recovery. The fake future completes from its queue state, and the fake executor has no ThreadPool shutdown behavior. The real provider timeout/cleanup path is outside this new probe.

## Source, chronology and composition

The original 39-test command/log/exit/source hashes are in `existing-normal.*`; the exact executed runner is `run_existing.py`. `probe-v1.freeze.json` fixes source, four schedules and limits before its single invocation. The exact executed probe and its first stdout/stderr/exit records remain unchanged. Reviewer construction wiring errors (uncompiled AST helpers and missing factory globals) were corrected during static inspection before this freeze and first invocation. Both invocations exited 0; no candidate rerun/repair was needed.

`source-manifest.json` binds all 24 exported files to their Git blob, SHA256 and size. The original local export selected recursive imports from the four test roots; this public `materialize.py` was added afterwards to reconstruct exactly that fixed file list without publishing local paths or duplicating source bytes. Its verification is a file reconstruction, not another candidate execution.

A read-only `git merge-tree` of main `f0c5a280e69944bb49d81bd2df4f00c6f9b35bbe` and PR head produced clean tree `864641ddd3ad86677ebb61d4e4eb96278981d030`. All 24 exported files have identical blobs in that tree (`composition-identity.json`). This permits scoped source-result reuse only; it is not broad integration verification or authorization to merge into a future main. PR #8006 remains stacked on #7930/#7904, whose agreement and integration requirements remain separate.

## Reproduce in a fresh output directory

Preserve the published first-run files. With a local repository containing pinned head `66ba74f...`, copy only `source-manifest.json`, `materialize.py`, `run_existing.py` and `probe_main_loop.py` into a new directory. Then run:

```sh
python3 -B materialize.py --repo /path/to/agent-interface
python3 -B run_existing.py
python3 -B probe_main_loop.py
```

Use Python 3.12 with Pillow and NumPy already available. No game/model/input allocation is needed or implied. Both reconstruction and execution refuse to overwrite the relevant existing output paths. This evidence package is additive, has no test-discovery filenames or runtime imports, and changes no production source or workflow.
