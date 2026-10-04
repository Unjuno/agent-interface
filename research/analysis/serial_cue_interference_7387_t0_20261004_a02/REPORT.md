# Issue #7387 A02 — method-scoped result

Disposition: **PASS_METHOD_SCOPED** for one finite, authored synthetic image-deck construction. The lag-by-task-demand model hypothesis remains **untested**.

The A02 candidate ran once in WSLc and emitted 144 matched cue trials, 288 paired presentations, 16 isolated controls and 1,280 PPM image files. A separately invoked frozen raw-only auditor ran once and returned `ok=true`, `errors=[]`, independently reconstructing all rows and image pixels. The 1,280 file paths contain five distinct pixel payloads (one blank frame and four glyphs), so this is not 1,280 distinct stimuli. Both invocations exited 0; retries=0. The exact freeze and run record are [FREEZE.json](FREEZE.json) and [RUN.md](RUN.md); all generated output and transcripts are retained under [formal_01](formal_01/).

The first A01 allocation remains a terminal output-directory STOP and contributes no data. A02 changed only candidate handling of an existing empty output mount and used a fresh output path. Preformal A02 construction checks passed 3/3. The separately frozen base candidate/auditor mutation suite passed a clean control and four corruptions (5/5 total). Construction failures and their repair chronology are retained in the respective READMEs.

WSLc warned that cgroup/swap limits are unsupported or unavailable. Requested `--memory 512M` is not evidence of enforcement. No speed, memory benefit, empirical GUI/model, action, safety, human-tempo or product claim follows. A model assay needs new owner/resource clearance, a preregistered fixed model/version and a powered T1 protocol.

## Repository validation

- `python -B research/analysis/check_index.py` first reported the expected missing A02 generated entry. Ran its provided `--write`, then reran check: `analysis index OK: 651 retained result/failure directories indexed`.
- `python -B -m unittest -v research.analysis.test_check_index`: 17/17 PASS.
- A workspace-index unittest invocation from the repository root failed because that module imports a sibling checker and expects `research/` as its working directory. The corrected `python -B -m unittest -v test_check_workspace_index` from `research/` passed 1/1.
- `python -B check_workspace_index.py --git-tree` from `research/`: 159 top-level directories reachable.
- `git diff --check`: PASS. These repository checks validate packaging/navigation, not model-facing hypothesis or live integration.
- An initial analysis-index `--write` in this sparse checkout displaced one manually authored #7371 custody note that had been placed inside the generated block. The PR diff exposed it; the note was restored in the manual navigation section, the generated block now only carries retained directories, and the index check passes without other directory removals.
- Read-only Git-object comparison verified all 1,303 tracked files under the two #7387 evidence directories are byte-identical to the local frozen sources, invocation transcripts, raw output, and audit. In particular, all 1,280 PPM Git blobs match their formal raw bytes exactly.
