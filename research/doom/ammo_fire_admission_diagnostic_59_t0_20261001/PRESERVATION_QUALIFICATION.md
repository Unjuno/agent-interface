# Preservation qualification (2026-10-02)

This additive note preserves the first retained diagnostic in PR #5932. It is a source/byte-custody review, not a new candidate run, independent raw-event audit, construction test, or live experiment. The eleven original package files, including the original SHA256SUMS, are unchanged.

## Retained result and limits

The recorded decision remains `PASS_DIAGNOSTIC_CONTRAST_SCOPED`, with retained auditor output `PASS_AMMO_FIRE_RAW_AUDIT`. The retained descriptive contrast is 0/1 completed keyset-confirmed attack holds with a sampled ammo decrease in v38 and 9/9 in v39. The other v39 starts remain one interrupted-after-keyset and one partial/unconfirmed attempt. These are unmatched historical episodes.

A sampled HUD ammo decrease during the declared attack-step envelope is a historical observed display/telemetry effect. It does not identify a causal shot, target hit, useful combat control, survival benefit, actual per-key held duration, robust live threat control, latency gain, human-tempo equivalence, or MAP01 completion. No new episode or replay was used to strengthen the result. Issue #59 remains open; this archive grants no input, game, model, container/GPU, host, or live-allocation authority.

## Static auditor caveat

The frozen `audit_ammo_fire_diagnostic.py` checks source hashes before assigning its local `all_errors = []`. If one of those source hashes mismatches, the earlier `all_errors.append(...)` references an uninitialized local and raises `UnboundLocalError` instead of recording the intended typed audit error. This is a source-inspection finding, not a newly executed mutation result. The reviewed source hashes match the freeze, so this branch does not contradict the retained matching-source output; it limits the auditor's error-path contract. Do not advertise the archived auditor as a generally fail-closed reusable verifier. Its original bytes and output are preserved; any repair requires a distinct successor rather than a rewrite or rerun of this allocation.

## Provenance and missing receipts

The review head is `5ecf8a68efc0a55a78abc48a45aa6af265b5ded1`. All eleven original file bytes match their Git blobs, and all ten entries of the original SHA256SUMS match. `PRESERVATION_CUSTODY.json` records those byte hashes without changing the original manifest.

The earlier in-branch freeze at `bc394f4ee59cf050b812568e5a1c94c2f1b51d2e` names main `0ea5f4a757775ee6a783ca12bc30000423cc41bf`. Its successor `2cff642ab7820501724f0c81cbf261035679a7e2` names `4b7fe7837e4ee8c0d035ebfbf52baf014f042295`. The historical reported freeze `02b6965b2d20e50098cbdf6d1b3ced887f4a12dd` remains retrievable and has the same five frozen source blobs as `2cff642`. Normal merge ancestry retains the earlier in-branch FREEZE.json version; do not squash away that distinct version without separately preserving it.

At immutable main `900c48368909a247ffd2b1b4dddd944cd6008d90`, the four v38/v39 event/report input blobs remain identical to the frozen inputs and their declared SHA-256 values. This confirms input identity only; it does not independently recompute the diagnostic. The package was absent from main at that snapshot.

RUN.json retains one candidate invocation, one independent audit, zero retries, exit-code and six-test assertions. Separate original process stdout/stderr/exit receipt files and a precise invocation UTC timestamp are not present in this package; RUN.json explicitly says the latter was not captured. Preserve these as ledger assertions with those limits, not freshly reconstructed process evidence. PROCESS.json retains the two path/preflight verification errors and their stated non-experimental corrections. This review did not invoke the package candidate, auditor, or construction tests, and did not rewrite or reconstruct missing receipts.
