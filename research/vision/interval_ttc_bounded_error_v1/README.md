# Bounded-error interval TTC (Issue #8157)

Construction A01 and A02 and the one-shot formal protocol live here. A01 used a pinned Python OCI image in WSL Arch + Podman and ran five arithmetic/fail-closed tests; A02 construction ran eight tests in the same pinned arm64 image through this Mac's OrbStack-compatible runtime. Neither construction stage was a corpus run. Formal details are frozen in `PROTOCOL_A02.md`. The formal allocation has not been invoked unless `results/FORMAL_A02/RUN_RECORD.json` says so.

Only finite synthetic radius traces are in scope. The candidate receives public timestamp/radius/bound/track histories. Truth, strata, split, and hazard labels stay in the auditor-only oracle. There is no GUI, game, model, user data, input, actuation, or runtime integration. A passing result cannot establish scene semantics or safety.
