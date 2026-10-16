# Distinct-XID replacement allocation #3000

Allocation: `golden-v3-identity-20260920-a2`
Image: `agent-interface-2994:20260920`
Digest: `sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`
Network: `none`

The original GTK window remained alive while the replacement was created. The captured IDs were distinct (old 2097155, replacement 4194307); only then was the original terminated.

Results:
- useful control: completed X11 dispatch, live GTK effect/capture, verified release
- source mismatch: `STALE_BINDING`, refused, backend emissions 0
- old target after replacement: `BACKEND_EXECUTION_FAILED`, `focus verification failed`, emissions 0, releases verified; the backend reports `failed_op_effect: unknown; may have emitted partial input`
- decision: `HOLD_IDENTITY_FAIL_CLOSED_NOT_PROVEN`

The distinct identity was achieved, but the runtime's own uncertainty about partial input means this is not a fail-closed PASS. Preserve this HOLD as evidence for the next repair.

Summary SHA-256: `77e2e1b22cf0afa3f5ee764db5c3ac98994b194b9903978306d6a62e5c100b9c`
Runner SHA-256: `f21e0711c131c10e556674d65bcead62b2a253bd4a4e5f4000143c9cdf98a682`
