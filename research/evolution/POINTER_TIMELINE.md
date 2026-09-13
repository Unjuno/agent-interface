# Three-domain pointer timeline: where the measured time went

Retrospective inspection of three actual assistant episodes finds that most time
from initial capture to final input-program terminal is **outside admitted
execution**, even though each episode uses the same measured session_v9 backend,
input_owner_v5 and executor_v3 source bytes. This prioritizes caller/observation
round trips and recovery over further motor-only tuning for these tasks.

| Domain / cohort | Capture → last terminal | Accepted execution | Outside accepted execution | Outside share |
|---|---:|---:|---:|---:|
| Inkscape pointer-desktop-01 | 74.494 s | 1.028 s | 73.466 s | 98.62% |
| OpenTTD guard-self-use-01 | 43.424 s | 1.255 s | 42.169 s | 97.11% |
| Mindustry build-self-use-01 | 145.184 s | 6.261 s | 138.923 s | 95.69% |

These are **three different known tasks**, not paired trials or a ranking of
domain difficulty. No average gain, significance test, latency tail or performance
promotion is justified. The percentages do not mean all outside time is removable.

## Method and evidence

[Report](results/pointer-timeline-01/report.json) records exact input/source hashes,
individual intervals and missing endpoints. [Analyzer](pointer_timeline_v1.py)
partitions each episode into initial capture→first admission, each accepted→terminal
interval, and each terminal→next admission gap. Their integer-nanosecond sum must
equal initial capture→last terminal exactly. Unmatched identities, negative or
overlapping intervals, and non-integer timestamps are rejected. Three synthetic
chronology controls exercise these rejection paths.

All subtractions are within one originating Python runtime process. Nine shared
backend/executor/lease source hashes are compared across the recorded manifests
and current immutable source files. Entry points, presentation wrappers, tasks,
oracles and model interaction histories are different; matching those nine files
does not establish identical whole-stack semantics or matched experimental arms.

The analyzer checks completed/released terminals and the archived evaluation event.
It does not replace the underlying frame/artifact auditors:
[Inkscape](../live_control/DESKTOP_POINTER.md),
[guarded OpenTTD](../openttd_task/GUARDED_PLACEMENT.md),
[Mindustry construction](../benchmark_discovery/MINDUSTRY_BUILD_SELF_USE.md).
Inkscape passes its legacy movement contract, not the later ±1-pixel precision
criterion. OpenTTD uses the corrected guarded episode, not the earlier weak score.
Mindustry's separate 600-tick delivery evaluation is outside this input-terminal
timeline and must remain separately reported in a future full-task comparison.

Outside time includes model decisions, tool dispatch, image display/review,
explicit clock requests, rejected requests, recovery and other work. Inkscape's
malformed chord rejection is retained in that interval; Mindustry's wrong block
selection and cancelled plan remain in the full timeline. There are no model
receipt/generation timestamps or recorded model identity/tokens in these raw
cohorts. None of the outside interval is relabelled as pure inference latency.

## Next comparison decision

The historical reference in `evaluation_plan.md` remains a historical study
reference. The newer default caller uses runtime27/socket11, optional checkpoint
features use runtime31/socket16, while these game/desktop pointer episodes use
direct stdin entry points over session_v9. We do not yet have a single tested
latest-stack adapter across these domains. Calling this completed shared-runtime
qualification would conceal that gap.

The next finite preparation should compare **caller delivery changes over fixed
backend semantics**, before bundling in motor or checkpoint changes:

1. Pin the existing session_v9 behavior, same tasks/oracles and full records as
   the initial reference. Preserve the separate Mindustry delivery phase.
2. Make one caller path persist requests/replies and present the returned image
   with its records, using the already researched combined-image pattern. Any
   clock operation must retain its distinction from a fresh observation; no
   silent input retry or refreshed observation authority is permitted.
3. First verify prefix retention, request identity, cancellation/release, stale
   rejection and oracle equivalence in all three adapters. This is integration
   readiness, not performance evidence. Freeze adapter hashes before live pairs.
4. Then register new counterbalanced actual-use pairs with identical output
   limits and recorded model/settings where available. Retain failures/recovery;
   measure all outer calls, initial feedback, final task result and runtime versus
   outside intervals. Missing model tokens/endpoints stay missing.

Do not compare a replayed successful route against a full assistant baseline,
silently replace v9 by v16 in only one arm, count raw JSON reduction as token
savings, or nominate Research Freeze from these three successful tasks. Broader
fresh/stress exposure and the bundle/frontier study remain open.

Reproduction: `python3 research/evolution/pointer_timeline_v1.py` creates its new
result directory and refuses an existing one. To inspect the committed run, read
the report and verify listed input hashes; use a separately versioned output path
for a rerun. Generated historical CSV ledgers and their denominators are unchanged.
