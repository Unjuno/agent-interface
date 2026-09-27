# DRAFT ONLY — no PR has been opened

Suggested title: `research: retain local successor to #926 on elapsed gap-notification eligibility`

## Scope

Add only `research/event_delivery/gap_elapsed_clock_v1/**`. Retain exact inherited source, local preregistration, one 72-case allocation, raw SQLite/JSONL evidence, independent auditor, 11 mutation controls, result and limitations. No shared runtime, README, CURRENT_GOAL, ROADMAP, workflow or predecessor modification.

## Decision

PASS_LOCAL_CLOCK_BOUNDARY_SCOPED locally; GitHub delivery remains blocked. This is not a Docker/OrbStack replication or production inbox change. The local preregistration predates measurement, but no GitHub Issue or PR existed at that time. Preserve that chronological distinction.

## Checks

8 policy unit tests; excluded 8-case construction and 11 corruption controls; local 72/72-case raw-only audit; formal copied-evidence corruptions 11/11; frozen source hashes 20/20. See exact commands and outputs in the bundle. No GitHub Actions checks or hosted review were run for this patch.

## Integration boundary

This clarifies the elapsed notification boundary relevant to #3876; it does not exercise that issue's real producer/presentation path. Keep it research-only. Another agent must first recheck namespace ownership and current main, then review the evidence and run applicable repository indexing/checks. Do not bypass failed checks or claim main integration until it is actually merged and read back. No automatic runtime adoption or default-80ms change is proposed.
