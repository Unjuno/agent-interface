# #2802 Allocation 07 — explicit bounded sequence-wrap semantics

## H
Within one stable producer generation, a bounded sequence counter can wrap without implying a generation reset if the counter modulus is explicit and the next value is exactly `(prev+1) mod modulus`. A strict linear-integer sequence policy rejects valid wrap; a timestamp-only policy falsely accepts missing wrapped records. Missing/changed modulus is UNKNOWN rather than inferred.

## T
Six scenarios ×3 cyclic repetitions=18 fresh producer subprocesses over stdout pipes: NORMAL_CONTIG, WRAP_CONTIG, WRAP_HEARTBEAT, WRAP_GAP, MISSING_MODULUS, LATE_WRAP. One generation per case; explicit modulus256 except the missing-modulus B control. Source bound20ms; late B30ms. One formal invocation after construction and GitHub source/gate freeze; reruns/replacements/tuning0.

## D
PASS_SEQUENCE_WRAP_BOUNDARY_SCOPED requires18/18 rows, all exits0, candidate SATISFIED9 / EXPIRED3 / UNKNOWN_GAP3 / UNKNOWN_COUNTER3; timestamp-only must SATISFY all12 WRAP_CONTIG/WRAP_HEARTBEAT/WRAP_GAP/MISSING_MODULUS provenance cases, including unsupported WRAP_GAP and MISSING_MODULUS; strict linear sequence must return UNKNOWN_ORDER on every valid-wrap case; audit errors=[] and8/8 corruption controls reject; source hashes unchanged.

## C
Explicit trusted local generation + modulus metadata; one producer per case. Modulus256 is a fixture contract, not inferred. Counter wrap is not generation rollover. No concurrency.

## U
Generation-ID reuse/forgery, multiple wraps under long retention, concurrent producers, reconnect, dropped transport beyond directed gap, cross-host clocks, GUI/model/task benefit, input authority, reliability rates and production promotion remain untested.
