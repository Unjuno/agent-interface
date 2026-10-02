# Temporal-effect identity T0 (Issue #6530)

Status: source package frozen by `FREEZE.json`; formal candidate and auditor have not run. Base is current `main` `a5756d9b3` (`2026-10-02`). Preregistration posted to Issue #6530 before source freeze.

## H/T/D/C/U

- **H:** Under a frozen `America/New_York` rule set and explicit typed intent, a semantic effect oracle detects a wrong instant/recurrence accepted by both string-only and offset-only comparisons, while refusing to invent a unique instant for an unresolved fold.
- **T:** A finite, model-free fixture comparison. Candidate derives classifications from intent and observed saved-event rows. A separately implemented raw-only auditor compares outputs with independently authored UTC truth. Cases cover ordinary local time, both fold occurrences, unresolved fold, spring gap, explicit zone versus fixed-offset input, post-entry zone change, a one-time event, daily 09:00 local versus fixed-UTC recurrence across the March 2026 transition, no-save and duplicate-effect controls. No GUI, account, invitation, or live calendar.
- **D:** Scoped method pass only if independently equivalent events are accepted; planted wrong instant/zone/recurrence/no-effect cases are rejected; wrong recurrence is rejected although both weaker baselines accept it; unresolved fold or unknown rule policy is UNKNOWN; gap is rejected; and the separate auditor agrees. Any false acceptance, silent disambiguation, or no baseline discrimination is FAIL_METHOD. Provenance/runtime/audit setup failure is STOP/HOLD, not a scientific outcome.
- **C:** Explicit persisted-event inspection or an application-specific documented rule may already be sufficient, making a new typed layer redundant.
- **U:** One zone/rule release and synthetic schema do not generalize to GUIs, all zones, floating/all-day events, or future rule changes; user intent remains the source of fold disambiguation.

## Freeze boundary

Construction tests must finish before formal source freeze. Pin `python:3.12-slim` by RepoDigest and verify TZDB release plus system zone file hash in the container. Candidate gets only fixture and source; auditor gets raw candidate output read-only and its independent expected table. Both use separate one-shot WSLc invocations with `--pull never --network none --cpus 1 --memory 512M`. Record the cgroup/swap warning; the memory request is not evidence of enforcement. No retries or substituted host result.

The independent UTC expectations are March 7/8/9 2026 09:00 America/New_York = 14:00Z/13:00Z/13:00Z and November 1 2026 01:30 fold=0/fold=1 = 05:30Z/06:30Z. The recurring fixed-UTC planted error is 14:00Z on March 8 and 9. The local fixed image preflight observed TZDB `2026c`, `tzdata.zi` SHA-256 `af5c1d3bebe136d372c131bb1a45725f955a8cc2a5ae2fc5a31d3b372e145f49`, and `America/New_York` SHA-256 `e9ed07d7bee0c76a9d442d091ef1f01668fee7c4f26014c0a868b19fe6c18a95`; formal preflight must revalidate before source is frozen.

## Evidence status

Source files are frozen by `FREEZE.json` content hashes; the source commit binding remains explicitly pending until the source commit and follow-on freeze commit are created. Candidate invocations: 0. Auditor invocations: 0. The environment-only image preflight and host construction check are not formal experiment results. No claim about application behavior is made. Formal invocation remains STOP until WSLc session access is restored; no retry is authorized.
