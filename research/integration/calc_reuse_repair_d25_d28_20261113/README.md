# Calc sequential development: D25 failure through D28 scoped repair

These four new attempts extend [D24](../calc_phase_lifecycle_d24_20261113/README.md).
They are sequential development qualifications, **not a matched efficiency
comparison**. All four first outcomes are retained, including the D25 failure.
Runtime base is 1bd8a3998fc6f1595b21455dc5fce3c10d76ff8d; each attempt freezes its
distinct private research adapter. No runtime or runnable code changes are
introduced by this report.

| Attempt | Result | Provider calls | Input tokens (cached subset) | Output tokens | Outer invocation seconds |
|---|---|---:|---:|---:|---:|
| D25 | Two-phase qualification failed | 2 | 25,760 (0) | 124 | 15.4157082 |
| D26 | Two tasks in one session, scoped pass | 2 | 25,797 (12,160) | 156 | 15.9463816 |
| D27 | Location hint reused, scoped pass | 1 | 12,203 (0) | 62 | 12.5840522 |
| D28 | Temporary obstruction refused, one repair, later reuse; scoped pass | 2 | 25,775 (12,160) | 124 | 17.0929067 |

Same existing pinned WSLc Calc image, Windows host, gpt-6.1-sol low and known
three-digit task family as D24. CPU 1 and 1 GiB requested; swap limiting is
unsupported. Outer monotonic intervals include launcher preflight and cleanup,
but exclude packet/source preparation and later audit. Cached input is a subset
of input tokens, not an additional amount. Provider sent turn/start counts
match response counts. Conditions, call counts and cache state differ; neither
time differences nor token totals establish a causal speedup or general score.

## What changed and what the evidence supports

D25 completed 538/726, then stopped at SAFE_YIELD/unknown_state with zero second
graph transitions. The second phase had already made its preliminary cell click;
this is not a blanket no-input result. Retained observations 33/34 show the name
box already saying A1 while the earlier frame still has the old A3 selection
border; the later frame shows the A1 border and formula 538. Both cell regions
changed while context and name-box crops matched. This explains the initial
pixel-predicate failure. The retained first failure is not relabelled by repair.

D26 adds at most six read-only captures within 300 ms and requires consecutive
matching cell/context/formula crops before using the selected source. It does
not grant input authority or prove indefinite stability. The second phase took
three observations. Both 538/726 and 419/853 were independently parsed from their
saved FODS snapshots; the second baseline hash equals the first saved hash.
Both phases have the same owner/scope and verified neutral release. Final owner
close and X key/button readback were neutral.

D27 retains a location hint from the first model answer. The second phase checks
scope, binding, revision, geometry, later observation and small image patches,
then uses fresh native references and normal action admission. It made no second
provider request. Two distinct saved effects and neutral release passed. This
is location reuse; each phase still constructs a CalcComposition, so it is NOT
compiled-plan reuse. Patch matching is not a general semantic identity proof.

D28 places an 8x8 magenta override-redirect obstruction over the hint's field
patch in the private X server. Reuse refused with target_patch_changed. Backend
emissions stayed 23→23, saved hash was unchanged, and readback was neutral.
The experiment harness then removed the obstruction. One predeclared grounding
call repaired the hint; 419/853 and subsequent reuse at 682/947 both passed saved
effect/release checks in the same owner. This is bounded repair after a known
temporary obstruction removed by the harness, not autonomous removal or recovery
from arbitrary permanent UI changes. All three saved snapshots were parsed
independently, and each baseline joins the preceding saved snapshot.

All four attempts ended with verified owner release. D25 container exit was 1;
all other host/container exits were 0. Named containers and recorded host PIDs
were checked absent after successful runs. Arbitrary descendant lifetimes and
broader formatting collateral were not independently scored.

## Preservation and next decision

SUMMARY.json contains per-attempt usage, exits, private packet names and manifest
hashes. Frozen inputs and all result-manifest entries were read back without
mismatch. The authorized local host retains raw screenshots, provider protocol,
sources, conditions, operation receipts, saved documents and audits. Raw is not
republished here; hashes alone cannot recover it. D25/D26/D27/D28 manifests cover
266/380/377/545 files respectively; later additive diagnostics are separate.

**RETAIN the narrow composition result; HOLD general efficiency and completion
claims.** The next comparison must fix all arms and ordering together, include
preparation/failed attempts/cleanup and identical verifier assistance, and retain
the strongest genuine plain baseline. Genuine compiled-plan reuse, unassisted
semantic target identity, full collateral checks and arbitrary-change recovery
remain open. #57 and the full computer-control goal are not completed here.
