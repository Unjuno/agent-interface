# Uncertain ordinary-release censor repair — #59 T1 A03

## H / T / D / C / U

**H:** If typed-backend `up` raises after an XTest request may have reached the
server, omitting that attempt lets a later retry appear to locate the key-up
edge. An explicit uncertain-attempt event should prevent that false interval
and leave the admission for verified cleanup censoring.

**T:** Run the V11 plus typed-backend contract suite under its controlled
FakeDisplay harness and the reconciliation suite. The regression injects a
release error, a later successful retry, and a verified owner cleanup carrying
a keycode bracket. It requires the oracle to taint aliases sharing the
resolved keycode, ignore that bracket for those uncertain admissions, and
return only cleanup upper bounds. Without cleanup, the oracle must fail closed
with an open interval. Current source SHA256s
are frozen in `FREEZE.json`.

**D:** PASS if the failed release yields an authority-free
`input_release_rpc_error`, the successful retry is not treated as a state edge,
the cleanup result is censored with no lower bound, and all scoped tests pass.

**C:** The adapter can only report exceptions that reach its Python caller.
This does not prove which XTest requests a real server processed before an
exception, or establish physical keyboard state.

**U:** No real X server, external input, game, model, GUI, live recovery,
performance, or end-to-end safety result is established. This does not solve
the still-unassigned live #59 lane.

## Reproduction

```powershell
python research/doom/map01_release_error_censor_repair_59_t1_a03_20261004/run_oracle_tests.py
python research/doom/map01_release_receipt_repair_59_t1_a01_20261004/run_v11_unit_fake_xlib.py
python research/doom/map01_release_error_censor_repair_59_t1_a03_20261004/probe_integration.py
python research/doom/map01_release_error_censor_repair_59_t1_a03_20261004/audit.py
```
