# WSLc typed-policy replay portability A03 — 2026-10-13

## H / T / D / C / U

**H.** A direct typed-signal adapter that calls the exact current-main `ObservableSignalGuard` can reproduce selected retained V39 health/ammo policy outcomes inside a pinned Python image on WSLc; an independently written raw-only auditor will reconstruct the same outcomes, without artifact extraction or input authority.

**T.** One WSLc run (allocation `WSLC-TYPED-POLICY-REPLAY-A03-20261013-01`) against source main `964c9197d5083ab55ea7fdc9105427623e89e677`, using the exact guard Git blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`; replay four selected events from retained report/runtime JSONL. Pinned image `python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd`, `--pull never`, network disabled, 1 CPU and 512M requested, C:-hosted read-only `/input`, dedicated writable `/out`, `--rm`, CID file, 60-second host deadline and 20-second per-stage deadlines. Candidate and auditor each ran once; retries 0.

**D.** `PASS_PORTABILITY_SCOPED`: candidate and audit exited 0; selected report/typed signals and guard outcomes matched for all four rows; soft events were sequences 96 and 160; unknown invalidations were 99 and 170; no input authority was granted; and a scoped query by the exact 64-character CID found no remaining container.

**C.** The adapter is a small construction harness around the production pure guard. The independent auditor implements the outcome rules separately and does not import candidate or guard code. Two pre-candidate attempts were retained: A01 stopped on host output decoding; A02 stopped because its pinned image was absent with `--pull never`. A03 changed only output capture, selected an image digest evidenced by a same-host prior WSLc run, and moved bind paths to C: after a separate D:-mount failure was recorded elsewhere. A03 is a fresh allocation; A01/A02 remain unchanged.

**U.** This is a replay of four selected rows, not production-controller integration. No game, model, GUI, OS input, task effect, live invalidation delivery, recovery, survival or task success was tested. The source report exposes two selected soft rows although its cumulative soft-event total is three, so this replay does not reconstruct every counted soft event. WSLc warned that swap-limit capabilities were unavailable; the configured 512M is not evidence of effective memory enforcement. No Docker comparison, cost or memory claim follows.

## Result details

The candidate produced `SOFT_CHANGED` for ammo at 96 and 160 and `UNKNOWN/source_expired` for health at 99 and 170. The typed event preceded artifact readiness by 44.642, 49.454, 53.500 and 45.435 ms respectively in this retained trace. The auditor independently reconstructed the status/reason from source values, thresholds, sequence, binding, capture age and signal value. Candidate and audit both report authority false for every row.

The WSLc command returned 0 in 0.500 seconds; candidate and auditor outputs were present. The container CID was `6a70d0de613ee39e06d105d732f9b4fd04a8384f105cffd4c1a4a7fff25e9fa7`, and the exact-ID cleanup query returned no rows. Host observed stderr warning: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.`

## Reproduction

From the allocation root, execute the frozen `invoke_once.py` exactly once. It invokes the candidate and independent auditor inside one WSLc container and writes raw stdout/stderr, JSON results, CID, run receipt, and scoped absence receipt under `output/`. Do not re-run allocation A03. For saved-data verification without WSLc, run `python -B candidate.py input/report.json input/events.jsonl input/observable_signal_guard_v2.py /tmp/candidate.json`, then run `python -B auditor.py input/report.json input/events.jsonl /tmp/candidate.json /tmp/audit.json`; these are reproductions outside WSLc and do not establish WSLc behavior.

`freeze.json` binds source/input hashes and the command; `SHA256SUMS.txt` binds the retained package files. `prior_stops/` preserves the A01/A02 freeze and STOP records. No image was pulled, no global container listing was issued, and no unrelated container was inspected or changed.
