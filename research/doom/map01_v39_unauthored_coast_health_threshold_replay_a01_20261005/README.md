# V39 unauthored-coast health-threshold replay A01 (#59)

## Result

The independent raw-only audit passes 12 checks over 45 typed observations
during A04 decision 5's pending planner turn. In this one retained trace,
health-loss thresholds of 5, 10, 15, 20, and 25 points would first have crossed
with approximately 11.990, 10.780, 5.436, 5.436, and 0.354 seconds remaining
before the original planner terminal, respectively. These are timing
counterfactuals only: no turn was interrupted and no replacement answer was
obtained.

The A04 final-action contract allowed at most 20 points of health loss from
source 30. Health was 10 at sequence 243 (exactly 20 points lost, still within
that bound), then 4 at sequence 261 (26 lost); the pending answer completed
shortly afterward and was rejected. The current V39 path explicitly uses
`unauthored_coast_no_policy` when no model-authored cover exists, so it does not
publish a health invalidation for that empty fallback. One 10-point trigger
would have appeared early in this trace, but this analysis does not establish
that interrupting then would improve feedback, control, or survival.

Decision 4 supplies one within-run negative control: the authored cover was
canceled on `health:source_expired` while health stayed 30→30. A loss-based
threshold would not have fired on that sample. This single quiet interval does
not estimate a false-trigger rate.

## H / T / D / C / U

- **H:** A bounded health-loss trigger during unauthored coast may notify the
  controller that the pending answer is likely to fail its existing health
  validity predicate before the model returns. There may be a useful trigger
  window between immediate interruption (risking liveness) and the existing
  late final-admission rejection.
- **T:** Replay the 45 typed-health observations captured after A04 decision 5's
  planner start and through its observed terminal. Sweep absolute health-loss
  thresholds 5/10/15/20/25 from the typed source value 30. Compare against the
  existing 20-point final-action bound, and check decision 4's unchanged-health
  expiry as a negative control. The source A04 archive, event stream, report,
  source manifest, and their hash manifests are retained under `input/a04/`.
- **D:** `PASS_A04_TRACE_REPLAY_AUDIT` requires source-member hashes to match
  A04's retained manifests, ordered pending observations, independent threshold
  reconstruction, the 20-point final-action rejection, and no negative-control
  trigger at unchanged health.
- **C:** One posthoc replay of A04, whose live run was already completed and is
  preserved in Draft PR #7990. Thresholds were selected after inspecting that
  trace. This is not a new allocation or prospective comparison.
- **U:** The replay does not show that an interruption would arrive before
  useful control is lost, produce a useful model response, authorize input,
  reduce damage, improve task progress, prevent death, or complete MAP01. One
  unchanged interval cannot estimate false interruption frequency or
  liveness. No threshold is adopted. A fresh, authorized current-main live
  exposure remains required.

## Reproduction

Run from the repository root with the Python standard library and a fresh output
directory:

```sh
out_dir=$(mktemp -d)
RESULT_DIR="$out_dir" python3 research/doom/map01_v39_unauthored_coast_health_threshold_replay_a01_20261005/candidate.py
RESULT_DIR="$out_dir" python3 research/doom/map01_v39_unauthored_coast_health_threshold_replay_a01_20261005/audit.py
```

Both programs use exclusive creation and refuse to replace retained output.
The candidate and auditor use the selected 45 observations directly from the
pinned event stream, rather than a hand-entered summary. Retained execution
outputs are under `results/a01/` through `results/a04/`. A02 is a
deterministic reproduction after adding source-manifest checks, not a second
live trial. A02's candidate bytes match A01 exactly; its auditor still resolved
the default A01 candidate path. A03 is the authoritative path-bound replay:
the auditor fix reads the candidate from its own `RESULT_DIR`, and the 16-check
A03 audit passes. After the branch rebased onto main `307b9e2f`, A04 repeated
the same frozen trace against a fresh output directory; the current V39
controller source hash remained `f76c618f5eedbe2c301eecb67c36c9064ec0de035009d0be6f8610bb1d808dc8`.
The A04 path-bound candidate/audit pair is the latest retained verification.

| Health-loss trigger | First sampled health | Time from planner start | Time remaining to original terminal |
|---:|---:|---:|---:|
| 5 points | 24 | 0.711 s | 11.990 s |
| 10 points | 18 | 1.921 s | 10.780 s |
| 15 points | 10 | 7.265 s | 5.436 s |
| 20 points | 10 | 7.265 s | 5.436 s |
| 25 points | 4 | 12.347 s | 0.354 s |

Health is sampled at discrete event boundaries, so multiple thresholds can
share a first observed crossing. The existing final-action rule rejects only
when loss is greater than 20 points; health 10 is exactly 20 points below
source and remains within that bound.

Inputs are extracted from the redacted public A04 evidence in [Draft PR
#7990](https://github.com/Unjuno/agent-interface/pull/7990), head
`3c6862937f30a22aad6380699f23da92d5d2c6f9`. The source archive SHA-256 is
`b6e8529a51e89e6f1c51374fbd27f121bab594c92014ee2fe73aa2f94ef98163`; the
included events and report match A04's retained `RAW_SHA256SUMS.txt`, and that
manifest matches the A04 package checksum list. Only the event stream, report,
freeze, result, audit, source manifest, and checksum manifests needed to
reproduce and audit this replay are duplicated here; the 68 MB raw archive is
not duplicated.

The A04 trial used controller source
`10a80334ef21b5dadd5d160ceec11ff2400f6b30ea8b55ffa0aeab3dde832f29`. Selected
main for this replay is `95316efef54b092fc2f0264539223830cdb9ba21`; its V39
controller is `f76c618f5eedbe2c301eecb67c36c9064ec0de035009d0be6f8610bb1d808dc8`.
The checked source diff is retained in `CURRENT_MAIN_SOURCE_DIFF.txt`: the only
V39 controller change between A04's base and selected main is the terminal
release race accepting `completed`/`expired` only with independently verified
empty release. This replay invokes neither controller version.

The computer-control live lane remains unassigned. No live game, model, GUI,
X11, or OS input was invoked by this replay. The A04 episode itself ended
unfinished, alive at the decision cap, with zero kills, no exit, and no
independent scorer progress.
