# Allocation v4 — independent auditor STOP

Candidate allocation `MAP01-HELD-OCCUPANCY-FULLTRACE-V4-20261002-01` completed
both inputs once (v38: 11 hold rows; v39: 29 hold rows, including one
cancel/ack-race row). Candidate outputs are `v38.json` and `v39.json`; their
source identities are unchanged.

The separately frozen v4 raw-only auditor was invoked once:

```text
python3 research/doom/audit_map01_held_input_occupancy_fulltrace_v4.py \
  --repo . \
  --out-dir research/doom/results/map01-held-input-occupancy-fulltrace-v4
```

It stopped on the first (v38) output before completing reconstruction:

```text
KeyError: 'no_input_before_admission'
```

Normal-completion candidate rows legitimately omit this false-by-default
classification field. This is an auditor implementation defect, not evidence
against the candidate data. Auditor invocations=1, successful full audits=0,
retry of v4 auditor=0. The frozen auditor, its source hash in the v4 FREEZE,
and both candidate outputs remain unchanged. A new auditor-only successor may
default omitted normal-row flags to false and independently audit both original
outputs; candidate must not be rerun.
