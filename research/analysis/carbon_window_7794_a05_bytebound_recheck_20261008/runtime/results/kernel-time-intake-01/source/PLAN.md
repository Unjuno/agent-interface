# Issue #5215 — temporal receipt boundary probe

Allocation: `kernel-receipt-time-5215-20260928-01`
Frozen main: `46416bc09283ad268c66e5327309f28fddbdf45f`
Branch: `research/kernel-receipt-time-5215-20260928`

## H / T / D / C / U

**H.** The current platform-neutral kernel may accept a terminal execution
receipt ending at or after the authority lease deadline, and may accept a
matching effect receipt timestamped before the execution ends.

**T.** Against the frozen, unmodified `runtime/kernel` sources, construct one
valid lifecycle and vary only receipt timestamps across valid and boundary
cases. Preserve exact source blob IDs and SHA-256 hashes, probe output and an
independent arithmetic audit. CPU only; no Docker, GPU, model, GUI, provider,
or network experiment.

**D.** `PASS_TEMPORAL_RECEIPT_GAP_SCOPED` if one or more invalid temporal cases
are accepted and all valid controls are accepted, with identifier mismatch
refused. `NO_GAP_OBSERVED` if invalid cases are all refused while valid controls
are accepted. Any source drift or audit ambiguity is `HOLD`.

**C.** Same command, source, request, identity, and release record; timestamps
alone vary. Independent audit evaluates integer inequalities from this frozen
plan and recorded outcomes, without importing kernel or probe code.

**U.** Contract-only result for the platform-neutral kernel. Does not test
clock-domain comparability, OS enforcement, real input timing, GUI effects,
application correctness, or production behavior.

## Frozen source identities

| File | Git blob | SHA-256 |
|---|---|---|
| `runtime/kernel/contracts.py` | `3d24fb5b28ae7812c71c6c1fedd3439d1473f0b8` | `f3287cb43ac7f557db7d35b754109432a1dcc9952a389784978963d28260ef9c` |
| `runtime/kernel/lifecycle.py` | `0735f1b2bc4f8c8c66a16cd0687a8b631c99f0b3` | `dbec526c4123333034bf761c6ef4e1d2e2746f809f84ce81e339420bff0e7ca0` |

## Cases

Lease deadline `1000`, begin-execution time `300`, execution start `500`,
normal end `700`, release observation `800`:

1. baseline execution end 700 / effect time 900 — accept;
2. execution end 999 — accept (strictly before lease expiry);
3. execution end 1000 — reject at exclusive lease boundary;
4. execution end 1001 — reject after expiry;
5. effect time 499 — reject before execution start;
6. effect time 699 — reject before execution end;
7. effect time 700 — reject at execution end (causally eligible);
8. effect time 701 — accept after execution end;
9. wrong command ID — reject.

No runtime source is changed in this allocation. Any observed gap is retained
as-is and requires a distinct successor before changing semantics.
