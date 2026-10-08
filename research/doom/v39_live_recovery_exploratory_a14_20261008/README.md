# Exploratory V39 live run A14 — freeze mismatch

## Disposition

**EXPLORATORY / PROTOCOL DEVIATION. This is not a valid preregistered #59 result.** The original freeze explicitly says “no planner turn or model call,” but the command accidentally launched the full six-decision controller. Keep the freeze unchanged and read `FREEZE_EXCEPTION.md` alongside it. The raw output is retained for diagnosis; none of its observations closes the live threat/recovery gate.

The run used the pinned `issue59-v39-live-env@sha256:b473b61c…` image, seed 991044, V15 measurement wrapper, and staged V39 source rooted at main `9d9c42c80f946762e8742ddb2739d07d33db136d`. Although the freeze described a marker-enabled diagnostic session source, the container actually mounted the ordinary staged `session_map01_v12.py` (SHA-256 `096fb996…`); no stage markers were present. See `FREEZE_EXCEPTION.md` and `DIAGNOSTIC_ADAPTER.json`. The tracked V39 controller, session wrapper, planner, guard, and executor sources were unchanged between the staged source at `708ca59a` and main at the run freeze. The later main commits through the package base add research records, not changes to those runtime files.

## What the retained run shows

The full controller completed six planner turns in about 40.0 seconds of model wall time. Two pending turns were interrupted and their answers rejected, both because the health source expired. At decision 2, health was 79 at source and 79 at invalidation against hard floor 69; ammo changed 43→42, remaining above its floor of 1. At decision 5, health was 53 both at source and invalidation against floor 33; ammo changed 41→39, again above 1. Both observations contain a visible enemy, but neither invalidation was caused by a typed health/ammo hard-boundary crossing. Thus the required threat-triggered gate was **not met**.

For both cancellations, the App Server reported the planner turn `interrupted` before the runtime published `input_released`. The release receipt independently verified no buttons, keys, unknown keys, or key-state errors remained. The release publication followed the interrupted completion by about 6–9 ms; this is one observation on the pre-#8392 interrupt-before-cancel ordering and says nothing about varied timing or a robust margin.

After the first expiry, the next fresh model answer was rejected as `REJECTED_ACTION_NOT_CURRENT`; a later turn was admitted with a retreat/fire action. No kill or MAP01 exit followed. The terminal score records zero deaths, zero kills, and no map exit in 43.46 seconds. The second expiry was the final decision, so it had no subsequent recovery turn.

The script `audit.py` independently recomputes these classifications from the retained report, protocol journal, runtime event stream, and image files. Its output is `AUDIT.json`; `RAW_SHA256SUMS.txt` covers all 370 raw files (47.31 MiB). The audit checks artifact consistency, not the protocol validity of the experiment; the protocol deviation remains disqualifying for efficacy claims.

Audit schema v2 also treats the declared diagnostic adapter hash as part of protocol validity. A model-free run with a missing or different startup source is classified as an exploratory protocol deviation even if zero planner turns occur. `test_audit.py` covers matching source, forbidden planner turns, and wrong/missing source cases.

## Earlier construction attempts

Related first outcomes are kept outside this directory in the local A05/A06/A09/A10/A11/A12/A13b output folders. A05 stopped before any model call because its container command omitted the `/out` mount (exit 127). A06 and A10 stopped during controller session startup before `turn/start`; A13b reproduced that stop. Separate V12 and V15 model-free session/fixture tests passed, including a same-seed construction check. These construction records do not authorize retrying or relabeling a consumed live run.

## Reproduce the audit

From this directory, run `python audit.py`. The script reads only this package and writes `AUDIT.json`; it does not start Docker, the game, or a model.
