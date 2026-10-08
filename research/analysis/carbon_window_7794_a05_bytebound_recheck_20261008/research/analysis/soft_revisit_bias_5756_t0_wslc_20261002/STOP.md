# Issue #6442 — pre-run STOP

**Disposition: `STOP_PARALLEL_HOST_ALLOCATION_ACTIVE`.** The formal candidate and independent auditor were each invoked zero times. No scientific result is available; this is a start-gate record only.

## Frozen identity and proposed method

- Issue: [#6442](https://github.com/Unjuno/agent-interface/issues/6442), successor to [#5756](https://github.com/Unjuno/agent-interface/issues/5756).
- Allocation: `SOFT-REVISIT-BIAS-5756-T0-20261002-01`.
- Main at the intake snapshot (`2026-10-02T02:29Z`): `eacb1346866f660d9d34eb36cd9691fd8184e5ff`. No executable candidate/auditor source or fixture was frozen.
- Planned branch/path: `research/soft-revisit-bias-5756-t0-wslc-20261002` / `research/analysis/soft_revisit_bias_5756_t0_wslc_20261002/`.
- Proposed test remains the Issue's 32 finite graphs × four policies (128 policy/fixture cases), with a 12-event cap; no candidate bytes, fixtures, schedules, or thresholds were formally frozen or executed.

## H / T / D / C / U carried from Issue #6442

- **H:** A bounded soft revisit penalty using visible inspection-confidence and child-revision cues recovers more targets behind incompletely inspected or changed children than hard visited-branch exclusion, without extra revisits on stable-complete controls; epoch changes still invalidate old observations.
- **T:** 32 deterministic graphs: 8 stable/complete, 8 partial-first-inspection, 8 same-epoch child-revision hints, 4 no-target/ambiguous-alias, and 4 with a forbidden non-reversible edge. Compare current-cue/no-memory, hard exclusion, soft revisit (max one revisit per branch), and safe exhaustive DFS; 12-event budget per policy/graph; separate raw-only audit after candidate exit 0.
- **D:** `PASS_METHOD_SCOPED` requires all 128 runs/events independently reconstructed, no hidden target claims or forbidden traversal, epoch reset, all five corruption controls rejected, soft finds at least 14/16 partial/revised targets while hard finds at most 2/16, zero soft revisits on stable controls, and zero audit errors. Safety/integrity defect is FAIL/STOP; clean unmet thresholds are HOLD.
- **C:** All graph labels, costs, confidence and revision hints are synthetic; authored fixtures may favor the soft policy. No natural GUI dynamics, perception noise, latency, or task effects are measured.
- **U:** One deterministic synthetic policy set on one WSLc host only. No model benefit, live GUI transfer, general optimality, real-world cost reduction, safety guarantee, or product claim.

## Gate evidence

The read-only Ubuntu/WSL2 inventory at `2026-10-02T02:28:38Z` found all eight known `native_mcp_v1.py` workers for the distinct `native-host-integration-03` allocation alive (PIDs 117, 144, 159, 172, 179, 195, 16672, 194102). The latest sampled CPU use was nonzero for PID 194102 (0.4%); the others sampled at 0.0%. Each held about 54 MiB RSS. These workers belong to a separate active allocation on the same host; no release or exclusive resource boundary was visible to this task.

The same snapshot showed global CPU and memory PSI `avg10/avg60/avg300=0.00`. This point sample does not prove the host is idle or remove the direct live-allocation conflict. The WSLc inventory showed only a pre-existing exited container (`adadf5c4bd8d`, exit 0, about four hours old), not a running container. WSL Ubuntu is a WSL2 distribution. No Docker command, WSLc container, candidate, construction container, or auditor was started for #6442.

Raw start-gate observations are retained in `HOST_GATE_EVIDENCE.txt`. No other worker or container was inspected, stopped, or modified.

## Disposition and resume condition

This STOP does not change the H/T/D/C/U hypothesis, the predecessor's 25-row `PASS_METHOD_SCOPED`, or the separate patch-leaving `FAIL_METHOD` in Draft PR #6412. It is not a null result, method failure, or evidence for/against soft revisit. Preserve this file and the raw observation unchanged. Resume only after a fresh exact-main/source/image/output check and an explicitly clear host/parallel-owner boundary; record any new allocation identity and conditions before a candidate invocation.
