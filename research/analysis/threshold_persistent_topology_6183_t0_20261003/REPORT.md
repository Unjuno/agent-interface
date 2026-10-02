# Result — Issue #6183 threshold-persistent topology T0

**Disposition: A03 passed the preregistered synthetic visual-method subgate;
application-effect transfer remains `HOLD`.** A01 is preserved as
`STOP_INFRA_PRE_CANDIDATE`; A02 passed only its fixed-route subtest; A03 added
scale, outline/hole, and auditor mutation controls. The issue does not establish
application effects because no eligible live/document effect oracle was tested.
No earlier outcome was overwritten; each allocation keeps its own identity and
outputs.

## What was tested

Eight deterministic 9x9 grayscale route fixtures were scored by a pixel
template-distance baseline, a single-threshold 4-neighbor endpoint-connectivity
baseline, and a four-threshold persistence rule. Candidate code saw pixels and
case IDs only. The independent auditor read separately stored visual labels,
replayed all three algorithms with a different flood-fill implementation,
compared metrics, and checked that every application-effect result remained
`UNKNOWN`.

## Observed result

| Method | Correct on determinate cases | Coverage on determinate cases | False confident outputs |
|---|---:|---:|---:|
| Pixel-distance template | 4/6 | 5/6 (83.3%) | 3 |
| Single threshold (128) | 6/6 | 6/6 (100%) | 2 |
| Threshold persistence | 6/6 | 6/6 (100%) | 0 |

The persistence method returned `UNKNOWN` on the gray near-touch and occluded
gap. The one-pixel gap and disconnected crossing were classified `ABSENT`;
clear route, brightness-shift, and both visually identical twins were
`PRESENT`. The twin outputs are identical on all image-only method fields even
though their hidden graph labels differ. Every row's application effect is
`UNKNOWN`; visual presence was not promoted to effect certification. The raw
candidate and independently recomputed audit match across all 8 rows with zero
audit errors. A02 candidate and audit each exited 0, OOM=false; in-container
cgroup readings confirm 512 MiB and one CPU quota.

Blinding limitation: A02 mounted the package directory read-only, and that
directory also contained the auditor-only `labels.json`. The frozen candidate
code opens only `fixtures.json`, but the OS did not prevent it from opening the
label file. Therefore A02 provides code-path separation, not filesystem-level
isolation of expected labels. A03 uses separate candidate and auditor source
mounts so labels are physically unavailable to candidate code.

The narrow preregistered subtest gate is met: all six determinate visual cases
are correct, coverage is 100%, ambiguous near-touch/occlusion abstain, false
confident outputs are strictly fewer than both baselines, hidden-graph twins
have identical visual outputs and no application effect is certified. The
baseline error counts include two ambiguous cases for the single-threshold and
pixel baseline; the pixel method additionally misses the disconnected
crossing through an `UNKNOWN` output on a determinate case.

The Issue-level clarified gate is **not** met. The Issue calls for mutation
controls and its proposed experiment includes scale sensitivity and both route
and outline predicates. This A02 contains no auditor corruption/mutation
challenge, no scaled fixture variant, and no outline/hole predicate. These are
not retroactively added to the frozen run and no post-hoc test is being passed
off as preregistered. A03 prospectively tested those missing synthetic
dimensions in a distinct allocation.

## A03 scale/outline/mutation follow-up

A03 tested 20 image-only rows: ten authored route/outline rasters at 1x and
exact nearest-neighbor 2x. Candidate and auditor used physically separate
read-only source mounts; candidate mount contained only candidate code and
pixel fixtures. Candidate/auditor each ran once in separate pinned-image
containers, exit 0, OOM=false. Independent replay errors were zero.

| Method | Correct / coverage on 14 determinate rows | False confident outputs |
|---|---:|---:|
| Pixel-distance template | 8/14; 12/14 covered | 10 |
| Single threshold | 14/14; 14/14 covered | 6 |
| Threshold persistence | 14/14; 14/14 covered | 0 |

All ten 1x/2x pairs retained identical visual outputs. The four auditor
corruptions (omitted row, duplicate id, flipped decision, fabricated effect)
were each rejected for the intended error. Near-touch and gray outline closure
returned `UNKNOWN`; clear route and closed outline were `PRESENT`; gaps and
disconnected crossing were `ABSENT`. All 20 application-effect fields remained
`UNKNOWN`, including visually identical twins with differing hidden-graph
labels. Thus A03 passes its prospective synthetic method gate, not an app-effect
gate.

The clarified Issue boundary still requires a separate application/document
oracle before semantic transfer. No real GUI, saved document, game, model, or
user task was tested here. Therefore the method result is useful but
application-effect transfer and issue closure remain on HOLD.

## Interpretation and limits

This supports only hand-authored synthetic visual-predicate discrimination.
Simple single-threshold topology matched persistence on all determinate A02
and A03 cases; observed gains came from abstaining on authored ambiguous
fixtures and the pixel baseline's template mismatch. Exact 2x nearest-neighbor
rescaling is not GUI scaling/antialiasing. Results depend on thresholds and
synthetic labels. No real GUI, route/document graph, app, game, model, temporal
effect, or user task was exercised. No application effect was detected or
verified. A typed application oracle is required before transfer.

## Reproduction and evidence

See `PREREGISTRATION.md`, `PREREGISTRATION_A03.md`, `RUN.json`, `A01_STOP.md`,
`CONSTRUCTION_A03.md`, and both `formal_a0{2,3}_orbstack_20261003/` folders for
freezes, commands, construction failure, first STOP, raw candidates,
independent audits, cgroup observations, and container identities. A02 source
freeze: `37ae40af2c1fc4daf70ce12511d9c44f8579f513`; A03 source freeze:
`757e11d58bb3c5a668aafdc89af628b0ddc03fde` (A03 command freeze:
`adb1c8887d3f76fe30856b7957a2e24951b5476d`). Verify package files with
`SHA256SUMS`.
