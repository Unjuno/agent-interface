# Issue #2447 — wrong-direction successor allocation 2447019

**Disposition: `STOP_PHASE_NOT_CONFIRMED` (construction-only); formal rows 0; retries 0.** The wrong-direction fault was not injected. This is neither PASS nor FAIL on that hypothesis.

## Frozen execution

The preregistered allocation used seed 2447019, class `drop`, temporal gate, requested heading 110°, the pinned local image `agent-interface-map01-lab:2447-preflight-20260927` (`sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`, linux/amd64), network disabled, read-only root/source/bundle/auditor, `/tmp` tmpfs, and a fresh writable evidence volume. The runner itself created its output directory. Frozen runner/auditor and source-bundle hashes matched in the preflight; all ten Python files parsed; source extracted; VizDoom 1.3.0 imported; exact output path was absent before the sole run.

Command:

```sh
mkdir -p /tmp/project
tar -xzf /bundle/source.tar.gz -C /tmp/project
python3 -B /runner/run_case.py --out /evidence/issue2447-wrong-direction-construction-2447019 --class drop --seed 2447019 --gate temporal_gate --heading 110 --source /tmp/project
```

Runner exit 0; `score.error=null`. Setup reached sector 165 at heading 114.2578° (requested 110°; error -4.2578°), with 18 setup decisions and verified empty release. The phase captured 13 frames and 12 adjacent pairs. Every pair met the frozen <=100ms and >=80-track eligibility requirements; gaps were 63.499559–89.100921ms and valid tracks 428–548. Independent LK recomputation found no qualifying vertical drop in any pair; all 12 were `NO_DROP`. The endpoint was also `NO_DROP` (347 tracks, median dy +4.1205px).

The runner correctly recorded `STOP_PHASE_NOT_CONFIRMED`, `handoff_after_wrong_direction=NOT_REACHED`, `third_subgoal_emitted=false`; no `next_subgoal` directory/action exists. Thus no faulted-turn visual effect was measured. It did not claim task or episode completion.

## Independent audit and raw package

A separate raw-only auditor recomputed all 12 image-pair metrics from retained PNGs and timestamps. Decision `STOP_PHASE_NOT_CONFIRMED`, `errors=[]`, 43/43 owner releases verified empty, retries 0. The audit JSON SHA-256 is `72b45f381d1c6b68b804238bfb5c23f3efe7acbb13dbe2a73c3bacbc9e4da2bf`.

Lossless raw ZIP `raw-evidence-2447019.zip`: 23 members, 1,799,086 bytes, SHA-256 `94d02af8dc8d2d1eec784c0c57e034e31536ac1875595f65c0f0cd79ca610601`. It contains the raw frames, timestamps, controller score/context, release/event records, and independent audit JSON. The predecessor 2447018 output-directory-collision STOP remains unchanged and unpooled.

## Scope

This exercises only the fail-closed phase-not-confirmed branch. It does not test wrong-direction visual detection, endpoint-vs-temporal comparison, fault sensitivity, false-positive rate, three-subgoal sequence, recovery, held-out transfer, MAP01 completion, or Issue #2447 acceptance. No retry or result substitution occurred.

