# A15 live authored-cover health-policy boundary result

**Disposition: HOLD for this allocation; no global work stop.** The single
preregistered A15 episode completed on 2026-10-09 from frozen source main
`a6343bb76e4dc0a4afa32a29c8a485a617faeff8` and experiment tree
`a588e11bc5bdd4ffad138bc3787b9dd13e5818ce`. Seed 990625, `gpt-5.6-luna`
low, 18/18 decisions, guest and app-server exit 0, 102.47 seconds, retry count
0. The result concerns this one allocation only.

The target authored-cover hard-health policy guard was not exposed (0 triggers),
so the hypothesis remains untested. A separate action-level health predicate
rejected one answer before executor admission at decision 3 (source health 88,
fresh health 78, maximum allowed decrease 8). This is not evidence that the
authored-cover policy guard fired. The episode recorded health 75–100, ammo
40–50, two kills, no death, no MAP01 exit, and no episode finish. No useful
scorer event occurred during model waits. The episode does not establish a
causal benefit, MAP01 completion, physical key state, or game input consumption.

The original frozen `AUDIT.json` remains unchanged with its original FAIL.
Its cancellation predicate expected a matching release event even for requests
with no admitted input lease. The additive cancellation reconciliation v2.1
and independent v3 instead account for all 18 cancellations: 12 have no active
lease and verified-empty terminal receipts; six active leases have matching
token-bound owner releases. All 68 per-key release transitions and 37 verified
empty terminals reconcile; no cancellation is unaccounted. The optional
`controller-failure.json` is absent, as expected after a clean controller exit.
This corrects the post-run custody interpretation without rewriting or
relabeling the original audit.

The separate action predicate and target policy guard remain distinct. A
follow-up needs a new, independently allocated episode whose preselected
exposure can bring active authored cover to its health floor while model
inference is pending. A15 is complete and must not be retried. This allocation
status does not stop unrelated authorized work; the shared Issue remains open.

Reviewable aggregate: `results-local/doom/map01-v39-live-threat-guard-a15-health-policy-guard-20261009/A15_RESULT_PUBLIC.json`.
The complete raw protocol and frame data remain in the local ignored
`results-local` tree and are not included in this public report.
