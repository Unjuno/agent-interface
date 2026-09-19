# MAP01 v12 physical occupancy R1 — independent audit

Run: 35443160602
Head: `68d5e9332c512dfe792c0872741fe3666830fd65`
Artifact: 10584416285
Artifact digest: `sha256:94dff5ec39475ef74d887660eccdc1d1ab13a8152671021cdfccd258ef3fa1b4`

## Audit disposition

`PASS_MAP01_V12_PHYSICAL_OCCUPANCY_R1_SCOPED`

The retained artifact was downloaded and independently inspected after workflow completion. The audit verified:

- frozen preflight passed;
- construction invoked once and passed;
- formal invoked once only after construction PASS;
- 3 fresh sessions completed and passed;
- 6 actuation edges total;
- all censor widths were below the 5 ms precision limit (maximum 0.559054 ms);
- all sessions had empty ownership after release;
- all sessions had post-sample-up and terminal completion;
- errors, reruns, replacements, tuning, authority expansions, and v3 physical promotions were zero;
- no broad production or user-facing claim is made.

The artifact and this record are immutable evidence for this execution identity. Any replication or broader claim requires a separate successor experiment.