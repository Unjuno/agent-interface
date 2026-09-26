# First-rung result — Issue #4588

Allocation: `confidence-trajectory-4588-first-rung-20260927-01`

Disposition: **PASS_SYNTHETIC_DISCRIMINATOR_ONLY**

Formal invocation: **1**, rows **84/84**, reruns/replacements/exclusions/tuning **0/0/0/0**.

## H/T/D/C/U and first outcome

- **H:** On an authored finite corpus, temporal confidence features can
  distinguish second-order aliases; raw acceleration may be noise-sensitive;
  `NO_OP` remains different from `YIELD`.
- **T:** Four fixed, authority-neutral rules were run once in OrbStack/Docker on
  the immutable `python:3.13-slim` image ID
  `sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0`
  (`linux/arm64`, Python 3.13.15), `--network none`, read-only root and source,
  separate writable results mount. The run used only the Python standard
  library. No model/provider, GUI/input, task/user data, or network was used.
- **D:** All frozen gates passed: raw-only audit errors `[]`; 8/8 effective
  copied-formal-row corruptions rejected; six second-order alias pairs met the
  per-pair gate; all six `NO_OP` cases were preserved; all 18 invalid-history
  cases explicitly used the current-only fallback; the acceleration/noise
  discriminator behaved as declared.
- **C:** The corpus and labels are deliberately authored finite fixtures; these
  counts are not natural event rates. Transparent rules are not a
  capacity-matched learned model. The audit is separately implemented by the
  same author, not independent human review.
- **U:** No real observation, model calibration, task success, cross-app
  generalization, human tempo, token/cost, action-authority, production-safety,
  or runtime-promotion claim follows.

| Policy | Typed correct / 84 | False `ACTION` | Precision | Recall |
|---|---:|---:|---:|---:|
| `CURRENT_ONLY` | 66 | 12 | 30/42 | 30/36 |
| `LEVEL_PLUS_VELOCITY` | 78 | 6 | 36/42 | 36/36 |
| `LEVEL_PLUS_VELOCITY_PLUS_ACCEL` | 78 | 6 | 36/42 | 36/36 |
| `SMOOTHED_TRAJECTORY` | 66 | 12 | 30/42 | 30/36 |

Velocity improves over current-only on this fixed corpus: 66→78 correct and
12→6 false executable decisions. Acceleration resolves all six second-order
alias pairs that current-only and velocity cannot distinguish, but its
oscillatory/noise rescue produces six false actions. Consequently it ties
velocity overall (78/84), not improves on it. The time-weighted smoother avoids
the six authored noise-stress false actions, but misses the low-confidence
rising cases and emits actions on the falling/overshoot families. All arms
produce `NO_OP` on the six self-correcting cases. Stale/missing/epoch-mismatched
history is invalidated, with all 18 cases recorded as current-only fallback;
no historical feature is consumed.

This is a narrow synthetic first rung. The evidence supports carrying velocity
as a candidate input for a later frozen shadow-mode transfer, but does not
justify raw acceleration without a separate robustness design. It does not
establish that any trajectory feature improves decisions on real model output.

## Execution and independent checks

Formal command (once):

```sh
docker run --pull=never --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev \
  --cidfile results/formal-container.cid \
  --mount type=bind,src="$PWD",dst=/src,readonly \
  --mount type=bind,src="$PWD/results",dst=/results \
  --workdir /src \
  sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0 \
  python -B run.py --freeze FREEZE.json --out /results/formal-01
```

The retained Docker inspection receipt identifies container
`306dbb97c234c83610cf4ff4e0ad7f5c5c3f3cd027e5c47f98e60229544bd5e5`, status
`exited`, exit `0`, network `none`, read-only root `true`; the stopped container
was removed only after its state receipt was saved. The runner retained exit 0,
PID, monotonic elapsed time, Python/platform identity, freeze hash, and raw hash.

Separate post-run container invocations used the same pinned image and
network/read-only constraints:

- `audit.py raw.jsonl`: 84 rows, 420 checks, `errors=[]`.
- `controls.py raw.jsonl`: eight effective copied-row mutations rejected 8/8.
- `gate.py raw.jsonl`: `PASS_SYNTHETIC_DISCRIMINATOR_ONLY`, all five frozen
  decision gates true.
- `python -B -m unittest -v test_audit`: 3 methods passed, including eight
  synthetic corruption regressions. Exact output is `results/formal-01/local-ci.txt`.
- `git diff --check`: run after packaging; its result is recorded with the PR
  validation chronology.

One post-run shell command attempted to hash the CID file using a misspelled
temporary directory path and returned nonzero after the experiment and tests
had already succeeded. The path was corrected; all listed artifact hashes and
the Docker state were then read successfully. No scientific command was
repeated or changed.

During packaging, the first checksum-manifest invocation used the study root
instead of the manifest's `results/`-relative directory; all nine entries
reported file-not-found. Re-running from `results/` verified every hash. The
first scoped `git diff --check` also caught two trailing spaces used for
Markdown hard breaks; they were removed. The corrected manifest and diff checks
are the ones used for publication. These were packaging-only failures; no
formal runner/audit command or frozen scientific source changed.

## Construction chronology

Before formal freeze, the first excluded construction unittest run exposed two
harness issues: one copied-row mutation was a no-op, and only 3/6 authored
acceleration-stress rows crossed the rescue threshold. The mutation was changed
to a value that differs from the positive row, and the fixed stress level was
raised before freezing so all six declared cases exercise the threshold. The
corrected preformal Docker unit suite passed. These are retained construction
corrections, not formal outcomes; no source or threshold changed after freeze.

## Integrity hashes

The raw JSONL is 66,906 bytes, 84 lines, SHA-256
`49f9204bde9fa72349da82a93a4bb0ffccd93cc213319070c94587ca5e1e8184`.
The freeze SHA-256 is
`7aec4be5251092c407e20935c450f4f988ac16092b159f8029f248dbe152512b`.
Artifact hashes are listed in `results/RESULT_SHA256SUMS`.

The experiment source and first outcome were published to Issue #4588 before
this results package. This package does not close the Issue or complete the
broader Local System-1 / desktop roadmap.
