# Report — V15 per-key owner identity revalidation A02

On exact PR #8065 head `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`, the
combined V15/per-key startup still selected the raw current V12 owner, not the
archived A01 InputOwner whose per-key telemetry the option requests. The
V12-per-key and default V15 controls selected their expected owner classes.
The 56-source independent PowerShell readback passed; the feature gate failed
at startup owner identity.

This resolves the alternative that the release-safety source update alone
fixed the cached-module mismatch. The imported owner class was inspected only;
no owner/session was constructed and no key operation occurred. Do not use
this V15/per-key route as A01 measurement evidence. A repair must compose the
instrumentation with current V3/V4 release safety and preserve release
ordering; forcing the archived owner alone is not enough. Per current-goal
r139, no threat-guard repair is justified before fresh live exposure. No such
exposure was authorized or run here.

Primary artifacts: `PLAN.json`, `FREEZE.json`, `FREEZE_REPAIR_01.json`,
`COMMANDS.json`, `RUN.json`, `AUDIT_REPAIR_01.json`, and the retained raw route
outputs in `results/current-head-4158-run02/`. `AUDIT_ATTEMPT_01.json` is the
preserved first auditor output; its false audit-integrity flag came from the
auditor's singleton-array handling, corrected without rerunning the candidate.
