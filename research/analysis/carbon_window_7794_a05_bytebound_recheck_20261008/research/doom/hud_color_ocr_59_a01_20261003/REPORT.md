# Issue #59 — color-channel OCR A01 result

**Scientific outcome: `FAIL_FINITE_REFERENCE_AGREEMENT_GATE`.** The selected
red-channel transform improves agreement with the archived typed health
reference, but it produces too many wrong nonempty values for a reliable reader.
Issue #59 remains open. Integrity/auditor PASS is not a semantic reader PASS.

| Phase / transform | Exact | Blank | Wrong nonempty | Rows |
| --- | ---: | ---: | ---: | ---: |
| Calibration / gray | 0 | 7 | 7 | 14 |
| Calibration / red | 4 | 1 | 9 | 14 |
| Calibration / red-excess | 3 | 7 | 4 | 14 |
| Evaluation / gray | 0 | 111 | 93 | 204 |
| Evaluation / selected red | 63 | 17 | 124 | 204 |

The 14 calibration rows selected red by the frozen maximum-exact-count rule.
The subsequent 204 rows achieved 30.88% exact agreement and 60.78% nonempty
wrong output. Exact agreement improved by 30.88 percentage points over the
paired gray baseline. The >=25-point gain condition passed; >=95% exact
agreement and <=1% nonempty wrong output both failed. These are finite row
counts, not independent-trial population estimates.

Evaluation OCR subprocess latency (not end-to-end live feedback latency):
gray median/p95/max 72.65/86.84/148.78 ms; red 72.27/83.42/133.69 ms. P95 uses
nearest rank over 204 calls. Conversion, resampling, PNG serialization, capture,
model and control latency are outside these per-call measurements.

## Evidence and chronology

`FREEZE.json` binds ten method files, hidden truth and both image-only manifests
before calibration. `SELECTION.json` was written after saved calibration audit
and before evaluation. Exactly one candidate and one saved-output auditor ran
for each phase: 42 calibration and 408 evaluation OCR calls, 450 total. There
were no scientific reruns. Candidate containers received only opaque crop IDs,
hashes and PNGs; truth/source files were mounted only in auditor containers.
The protocol author had previously inspected this episode, so this is not a
researcher-blind test or held-out-episode result.

Both container auditors verified source joins, all RGB/crop identities, row
membership, raw-text normalization and counts. Eight saved-evidence mutations
per phase were all rejected. `verify_result.py` checks the frozen source/input
hashes, selected-arm rule, saved audit results, container mounts/resources,
terminal states and chronology, then recomputes `RESULT.json` without OCR.
Audit logic and candidate logic have the same author; the separation is by
process, inputs and validation code, not by independent human authorship.

The image is `sha256:daab0718fb332540c9c7b1a4ada74f7741a01c8b6779b2bac1307bc0d6a41323`,
Ubuntu 24.04 arm64, Python 3.12.3, Pillow 10.2.0 and Tesseract 5.3.4. Raw records
retain engine versions and trained-data SHA-256. This is not a numerical
replication of the earlier macOS Tesseract 5.5.2 study.

All four scientific containers exited 0, without OOM, with network disabled,
read-only rootfs, capabilities dropped, no new privileges, 1 CPU, 512 MiB,
no swap and 64 PIDs. Saved cgroup files confirm actual bounds. Engine, source,
outputs and terminal inspections are retained for review. Local verification
receipts are in `local_ci/`.
All exact owned containers were terminal at closeout, and the owned VM was
successfully stopped; engine/image/files remain recoverable.

## Preserved setup failures and scope

The first image build in an isolated owned OrbStack VM failed before any OCR:
`bpf_prog_query(BPF_CGROUP_DEVICE) failed: operation not permitted`. Its complete
record is `setup/image_build.json`. The owned VM was stopped, switched to normal
mode, and restarted; the private Docker daemon was retained. A stale `/study`
path check also failed and is retained in `setup/normal_engine_inventory.json`.
After correcting normal-mode mount paths **before method freeze**, the second
image build succeeded. No other VM/container/engine was changed.

The [matching OrbStack issue](https://github.com/orbstack/orbstack/issues/2429)
informed that environment repair. Normal mode exposes macOS integration to the
VM; the candidate itself remains bounded by the recorded Docker mounts. This
is not a claim of a separate kernel/security boundary or an approved live
game/model allocation.

Reference values come from the same archived episode's WAD-specific extractor,
not independent human truth. Adjacent rows and sequence 151's reused `150.png`
are correlated. The test does not establish independent useful-feedback onset,
cause of health loss, matched controller benefit, bounded recovery, exact key
release or MAP01 completion. No shared/live lease was consumed or requested.

## Integration and next research boundary

Archive this negative result rather than deploy the selected transform.
Another reader needs a new additive protocol, independent labeling or a
separate episode where possible, and an explicit abstention/error gate. Do not
tune or repeat this frozen evaluation in place. The prior package at
`../results/issue59_v39_hud_ocr_posthoc_20261003_01/` remains exploratory; its
`EXECUTION_HISTORY.md` discloses earlier overwritten packaging outputs.

Saved-only verification from the repository root (requires Pillow):

```sh
python -B research/doom/hud_color_ocr_59_a01_20261003/verify_result.py
```

Do not run `build_inputs.py`, `freeze.py`, `choose.py` or `run_stage.py` against
the retained paths: their exclusive-create guards preserve the first outcomes.
