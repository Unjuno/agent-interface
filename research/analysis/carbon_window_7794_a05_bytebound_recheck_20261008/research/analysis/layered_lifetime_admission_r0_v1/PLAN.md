# Layered lifetime admission contract — R0

Task: `LAYERED-LIFETIME-ADMISSION-CONTRACT-R0-20260918-001`

## H
For independently stale-able binding, precondition, route, observation-cache and motor-calibration layers, a token with a declared dependency mask is valid exactly when all epochs in that mask remain current. A global epoch is safe but over-invalidates unrelated changes. A route-only epoch both misses stale non-route dependencies and over-invalidates route-independent tokens.

## T
Deterministic standard-library model. Enumerate all 31 non-empty dependency masks × all 32 changed-layer masks = 992 rows. Compare LAYERED_EPOCHS, GLOBAL_EPOCH and ROUTE_ONLY_EPOCH against a set-intersection oracle. One source-frozen formal invocation; independent audit and corruption controls.

## D
PASS iff layered/oracle mismatch0 and stale accepts0; global stale accepts0 with false invalidations>0; route-only stale accepts>0 and false invalidations>0; all five one-layer positive/negative controls pass; integrity passes; formal1/reruns0/replacements0/tuning0.

## C
Dependency masks may be wrong or incomplete; #165 owns discovery. Shared epochs remain legitimate when two mechanisms provably share a lifetime. This tests admission semantics, not final ABI structure.

## U
Synthetic currentness only; no natural invalidation rate, runtime latency, GUI/model/token/task or production claim.
