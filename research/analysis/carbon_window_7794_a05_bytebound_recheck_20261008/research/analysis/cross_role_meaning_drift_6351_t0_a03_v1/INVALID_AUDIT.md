# A03 audit disposition: INVALID

The candidate ran once and its bytes are preserved in `candidate.json`; the matching synthetic input is `raw.json`. The accompanying `audit.json` is also preserved as originally emitted, but must not be used for inference: its auditor compared only verifier, child, and epoch-conflict fields and omitted planner dispatch plus effect-owner release/effect. A04 independently audited all role fields without rerunning the candidate. See [`../cross_role_meaning_drift_6351_t0_a04_audit_v1/`](../cross_role_meaning_drift_6351_t0_a04_audit_v1/).
