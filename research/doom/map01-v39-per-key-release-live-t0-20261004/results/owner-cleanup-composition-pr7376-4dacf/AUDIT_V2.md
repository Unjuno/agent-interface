# Raw-only temporal re-audit

The original `audit.json` and `audit.py` remain unchanged as the historical V1 result. An independent review found that V1 trusted the component's `owner_cleanup_intervened` flag without checking the cleanup record's timestamp against the release-call interval.

V2 reads only the retained `candidate.raw.json`. It requires the sole verified cancellation-cleanup record's integer `verified_ns` to satisfy `release_call_started_ns <= verified_ns <= release_call_returned_ns`, and rejects inverted or missing intervals. The V1 output is not rewritten. The candidate, owner thread, Xlib/XTest harness, and formal allocation were not rerun.

## Result

`audit_v2.json` records `PASS_TEMPORAL_RECEIPT_BINDING_SCOPED`: 9/9 baseline checks and 8/8 mutation controls pass. The retained cleanup timestamp (`92007177502791`) falls inside the retained release-call bracket (`92007174484916` to `92007177543708`). The raw record SHA-256 is `6d0742bc740dee53a61c03c53eb39b7a01aa4f82f1b3ae74b04790be1ba52d90`; the auditor SHA-256 is `9a3243f940eed55188f7e15b561c76b4d4c3bf53b58bfa9f387eba0cc165d7cf`.

Run: `py -3 audit_v2.py`. This is a post-hoc audit of one deterministic fake-Xlib/XTest construction record. It is not live X11, physical-input, application-effect, task-control, or latency evidence.
