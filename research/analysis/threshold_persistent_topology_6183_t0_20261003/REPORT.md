# Result — Issue #6183 threshold-persistent topology T0

**Disposition: A02 passed its preregistered fixed-route subtest; Issue #6183
remains `HOLD_INCOMPLETE_SCOPE`.** This is not an Issue-level
`METHOD_PASS_SCOPED`. A01 is preserved as `STOP_INFRA_PRE_CANDIDATE`; its
candidate process never started. A02 was a separately frozen allocation after
a runner-only correction. No A01 outcome was overwritten, and no
candidate/auditor retry occurred within either allocation.

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
off as preregistered. The Issue remains open/HOLD pending an additive,
prospectively frozen follow-up or an explicit scope decision.

## Interpretation and limits

This supports only the narrow, hand-authored synthetic visual-predicate
comparison. It does not show that persistent topology is better than simple
connectivity on clean, determinate cases: both achieved 6/6 coverage/correctness
there. Its observed advantage is abstention on the two ambiguity fixtures.
The benefit over a single threshold depends on the authored gray-level
perturbations and the preregistered thresholds. No real GUI, route/document
graph, app, game, model, animation, theme, zoom, or user task was exercised.
No application effect was detected or verified. A typed application oracle
remains necessary before any transfer claim.

## Reproduction and evidence

See `PREREGISTRATION.md`, `RUN.json`, `A01_STOP.md`, and
`formal_a02_orbstack_20261003/topology-6183-a02/` for exact freeze, commands,
first STOP, raw candidate, independent audit, cgroup observations, and container
identities. The frozen implementation commit is
`8cf37e9d7ce174cb04f9b98a722f438cc310069d`; later commits add only execution
provenance and result reporting. Verify package files with `SHA256SUMS`.
