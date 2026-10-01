# Issue #5836 T0: request-bound trusted confirmation

Allocation: `trusted-confirmation-5836-t0-20261001-01`  
Base main: `49db21e330768800e8b3486203b70306f4e402f6`  
Branch/path: `research/5836-trusted-confirmation-t0-20261001` / `research/security/trusted_confirmation_5836_t0_20261001/`

## H/T/D/C/U

**H.** In a finite broker fixture, a separate confirmation channel with request-bound, single-use receipts rejects page/model forgery, stale or replayed grants, target/principal substitution, revocation, and lost-response retries while preserving a valid matched approval and denial path. This tests semantics only.

**T.** One deterministic CPU-only run in locally present `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Docker `desktop-linux`, network disabled, read-only root and source, bounded CPU/memory/PIDs. Compare page-text approval, request-bound replayable receipt, and independent-channel single-use receipt across 10 fixed cases. Then invoke the separate raw-only auditor once. No model, GUI, human subject, credential, payment, privilege, or external effect.

**D.** `PASS_METHOD_SCOPED` iff all 10 rows match the independent oracle; the trusted arm authorizes only the exact valid matched request; forged, stale/replayed, swapped, mismatched, revoked, denied cases cause zero authorization; lost response is not retried; weaker baselines expose the planted page-text and replay errors; and all five evidence mutations reject. Any unauthorized trusted authorization or retry is FAIL; incomplete/mismatched evidence is HOLD/STOP.

**C.** A broker-bound out-of-band approval without a rich receipt may suffice; request digest alone may suffice on immutable effects; existing capability/lease admission may already prevent these attacks. The weaker arms are deliberately finite and not production comparators.

**U.** Synthetic channel provenance cannot prove that a real OS/hardware display/input path is independent, authentic, comprehensible, accessible, or coercion-resistant. No real human preference or actual effect is measured. T0 does not close any downstream adoption or integration question.

Raw result and audit are generated under the local working copy before publication; their bytes are immutable once written. No GitHub workflow is used.
