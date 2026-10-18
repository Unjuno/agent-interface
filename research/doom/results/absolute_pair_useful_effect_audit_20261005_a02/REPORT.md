# Absolute-window useful-effect audit A02

## H — Hypothesis
The six retained 600 ms coast/pulse windows contain enough independent scorer data to classify positive objective progress, negative safety signals, or MAP01 exit before the deadline, and the pulse arm's per-key owner key-up receipts can be joined to the original release events.

## T — Treatment
An independently written raw-only auditor checks six frozen result and runtime records. It joins scorer samples to scorer-client updates by run ID and sample sequence, uses each sample's producer timestamp against the saved `[window_start_ns, window_end_ns)` boundary, and joins each explicit per-key release row to its owner-thread XTest KeyRelease/XSync receipt. No producer or game process was launched.

## D — Design and provenance
Three coast and three pulse cells from `research/doom/absolute_pair_59_4d74_20261004`; 48 raw input files are SHA-pinned in `FREEZE.json`. The auditor source hash and exact WSLc command are frozen there. WSLc ran cached image `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378` with `--pull never`, `--network none`, user 65534, one CPU and 512 MB, a read-only source mount and separate output mount.

A01 is retained in the sibling package `absolute_pair_useful_effect_audit_20261005/`. It failed because it compared complete score dictionaries, including result transport field `emit_ns` absent from `runtime/score.json`. A02 compares only the five predeclared semantic fields: kill count, death count, player-dead, episode-finished and map-exit. No raw inputs or scientific criteria changed.

## C — Result and interpretation
A02 passes the evidence-integrity gate with zero errors. It reconciles six 600 ms windows, 111 scorer samples, and six owner-thread key-up receipts to six explicit-up rows. All six final score records agree on the five semantic fields. In-window samples show zero positive progress signals (no kill increase, episode completion or map exit) and zero sampled negative safety signals (no death increase or player-dead) in both arms. Final kills/deaths are 0/0 in each cell.

The scorer-sample schema does not include health or ammunition. A separate additive A03 audit of the runtime typed-observation rows found 27 in-window HUD health/ammo observations joined to screenshot metadata: health stayed 97 and ammo stayed 48 in every sample. This establishes no typed health/ammo transition during these short windows; it does not show useful task progress or prove that the rendered images contained no other useful feedback. The six cells also do not support a causal or effectiveness comparison: there was no model and the scenario produced no positive or negative score event in either arm.

## U — Use and limits
This is a post-result raw-data audit, not a new allocation, matched recovery evaluation, live control result, or product claim. The owner-thread KeyRelease/XSync receipt bounds a server call; it does not verify physical key state or application effect. The result sharpens the next study requirement: create a changing, independently measurable threat/task-effect condition before assessing useful feedback or bounded recovery. It does not close issue #59.

## Retained first outcome and environment
A01's failure is unchanged. WSLc reported: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The audit makes no swap-enforcement claim. Raw stdout, stderr, exit code, command, input hashes and full cell details are retained in this directory.

## Delivery state
This package is delivered in pull request #7676: https://github.com/Unjuno/agent-interface/pull/7676. A concise result was also posted to issue #59.

## Current-main input reconciliation

All 48 frozen input blobs were independently rehashed from current `origin/main` at `52d2c7a7b6f4854d9d9de43d001a1d8ebfbfaacf`; `BASE_ALIGNMENT.json` records zero mismatches. The offline audit therefore applies to data available in the PR base without copying or rewriting the original study records.
