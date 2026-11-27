# Reverse-order matched Calc recovery comparison

This is a separately frozen, reverse-order counterpart to [i01/i02](../wslc_calc_matched_recovery_20261031/README.md). The same fixed 731/864 Calc fixture, candidate and one temporary 8x8 target obstruction were used. Both routes reject the stale target before mint/input, remove the test's own obstruction, capture again and make one fresh grounding call. The compiled route ran first, followed by fresh re-grounding. Each has its own persistent model session, gpt-6.1-sol requested low, 1 CPU / 1 GiB WSLc, network-disabled container and host-only model calls.

| Allocation | Route | Task interval | Launcher interval | Calls | Input (cached subset) | Output | Saved effect |
|---|---|---:|---:|---:|---:|---:|---|
| j01 | compiled | 9.280 s | 12.354 s | 2 | 25,763 (12,160) | 124 | exact 731/864 |
| j02 | fresh | 14.433 s | 16.757 s | 3 | 40,698 (21,504) | 186 | exact 731/864 |

Both had verified releases, empty final X key/button state and independent FODS checks. Across the two fixed-order pairs, median task intervals are 9.622 s compiled and 13.891 s fresh; median input is 25,771 vs 40,722 tokens. Input includes cached tokens; no monetary rates are inferred. The task interval starts before first model request and ends after owner close and saved-file scoring, excluding application/container startup and final cleanup. Launcher time includes launched processes but excludes fixture/source preparation and audit.

`public.zip` preserves fixed inputs, conditions, observations, usage, receipts, FODS and cleanup records. `audit.py` checks the pinned archive, source/candidate hashes, stale screenshot pixels, fresh image association, model call/session usage, releases and independently parses the whole saved FODS. `compare.py` runs both block auditors and checks matching candidate, source, image and separate model sessions before recounting. Run both using Python without optimization and Pillow. Omitted private model protocol journals and host path-bearing command lines are not independently audited.

These four runs use one fixed fixture, one intervention that the test removes, scripted Save, different route internals, differing provider/cache conditions and only two samples per route. They do not prove statistical significance, general speed or reliability, persistent-obstruction recovery, partial-input recovery, third-arm performance, MAP01 completion or project completion. Issue 57 remains open.
