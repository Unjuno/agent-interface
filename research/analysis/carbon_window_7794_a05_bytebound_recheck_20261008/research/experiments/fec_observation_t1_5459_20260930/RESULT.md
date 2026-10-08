# T1 result — `PASS_T1_DETERMINISTIC_TRANSPORT_CONSTRUCTION_ONLY`

## Executed comparison

The one-shot runner evaluated 64 six-slot erasure masks crossed with eight
frozen 0/2-round delay profiles: 512 matched traces per arm, 1,536 arm runs.
It also ran five semantic/fault modes across three arms (15 fault runs). The
independent audit re-decoded every delivered equation with a separate GF(2)
RREF implementation; `errors=[]` and the raw hash agrees.

| arm | confirmed windows | transmissions | completion rounds among confirmed |
|---|---:|---:|---|
| fixed two-repair | 128/512 (25.0%) | 3,072 | round 0: 24; round 2: 104 |
| systematic retransmit | 108/512 (21.09%) | 3,024 | round 0: 8; round 1: 18; round 2: 44; round 3: 38 |
| adaptive pair repair | 108/512 (21.09%) | 3,024 | same as retransmit in this toy |

On the four predeclared single-source-erasure/no-delay traces with both repair
slots available, fixed repair completed at round 0; retransmit and adaptive
repair completed at round 1. It used six versus five packets on those cases.
On the clean trace, adaptive and retransmit completed at round 0 with four
packets, versus six for fixed repair.

All three arms had zero false semantic confirmations in the 1,536 transport
runs. Across the 15 injected semantic cases, wrong generation, wrong window,
incomplete dependency manifest, and stale manifest hash all returned
`UNKNOWN` (3/3 arms each). In the corrupted-source control, the unauthenticated
packet was discarded; valid parity/retransmission recovered the true state,
which was independently confirmed in all three arms. This is recovery of a
correct state from redundant evidence, not acceptance of the corrupted row.

The global matched grid gave fixed repair 20 more confirmed windows at a cost
of 48 additional transmissions across 512 traces. Adaptive and retransmit had
identical totals here; the T1 result does not show an adaptive advantage over
ordinary retransmission outside the clean-window overhead comparison.

## Verification and retained deviations

- Frozen suite: `python -B -m unittest -v test_t1.py` — 5 tests passed.
- Candidate runner: `python -B run_t1.py` — exactly once; 1,536 trace runs,
  15 fault runs; raw SHA-256
  `1AD1B1037ACA9496E8617CCF70AA2F23B7E373C7754002DCF3100BF0D9EDDF6E`.
- Separate independent audit: `python -B audit_t1.py` — exactly once after
  runner exit 0; PASS, zero errors; same raw SHA.
- The first post-implementation test invocation found an auditor `NameError`
  (`Counter` was not imported; initial audit source hash
  `387BB26298BE971C34CFE343536192BED0AB8F7D7015B4D05D8094CDB08318A4`). The
  import was added, execution freeze updated, and the suite then passed. The
  one-shot candidate runner had not yet run at that point and was not repeated.
- Eleven retained artifact/source hashes are listed in `SHA256SUMS`.

## Scope

Host-only deterministic construction using CPython 3.12.10 on Windows. Docker
Desktop/OrbStack was not invoked: #5085 still requires an exact named shared
resource allocation. No real transport, RaptorQ implementation, observation
capture, model, GUI/X11, MAP01, GPU, or task-effect observer was used. The
pairwise XOR code, binary delay profiles, and deadline are synthetic; the
aggregate rates are not field reliability estimates. This does not establish
real observation freshness, security against a lying authenticator, physical
input occupancy, useful-feedback time, matched gameplay recovery, or product
benefit.
