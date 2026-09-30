# Issue #5215 — scoped temporal receipt result

Allocation `kernel-receipt-time-5215-20260928-01` ran once on frozen main
`46416bc09283ad268c66e5327309f28fddbdf45f`, Windows / CPython 3.11.9. No Docker,
GPU/CUDA, model, GUI/input, provider, or network experiment was used.

## H / T / D / C / U

**H.** Execution receipts ending at/after lease expiry, or effect receipts
timestamped before claimed execution completion, may be accepted by the
platform-neutral lifecycle.

**T.** One standard-library probe varied only receipt times for a fixed request,
source, identity and verified-empty release. Exact source blob and SHA-256 pins
are in `PLAN.md`. The frozen runtime files were not modified.

**D. `PASS_TEMPORAL_RECEIPT_GAP_SCOPED`.** The kernel accepted execution
completion at the exclusive lease deadline (1000) and after it (1001), although
lease expiry is checked at authorization and execution start. It also accepted
effect receipts at 499 (before execution starts at 500) and 699 (before
execution ends at 700). It accepted controls ending at 700 and 999, effects at
700 and 701, and rejected the wrong-command control. The independent arithmetic
audit reported zero control errors and four invalid temporal cases accepted.

| Case | Observed |
|---|---|
| execution end 700 / 999 | accepted |
| execution end 1000 / 1001 | accepted — lease-boundary gap |
| wrong command identity | rejected |
| effect time 499 / 699 | accepted — causal-order gap |
| effect time 700 / 701 | accepted |

The prior runner invocation without repository root on `PYTHONPATH` failed
before any case ran; the recorded experiment is the subsequent successful
single invocation with repository root on `PYTHONPATH`. No experimental case
was retried.

**C.** Identical request, command/manifest/lease/surface identity and release
receipt across cases; timestamps alone varied. `audit.py` is standard-library
only and imports neither candidate probe nor kernel. Its oracle checks valid
controls, the identity negative control, and whether any preregistered invalid
temporal case was accepted.

**U.** One host and the platform-neutral kernel v1 contract only. No backend
clock-domain relation, actual OS lease enforcement, real actuation timing, GUI
effect, application correctness, or end-to-end safety was tested. This result
does not establish that existing integrations violate an enforced runtime
lease; it establishes that this abstraction's receipt-ingest path does not
validate these temporal relations. A fix needs a successor allocation and
explicit handling of backend clock and delayed receipt semantics.

## Reproduction

```powershell
$env:PYTHONPATH='.'
python research\kernel_receipt_time_5215_20260928\probe.py
python research\kernel_receipt_time_5215_20260928\audit.py
```

Raw probe output is `probe-output.json`; independent audit output is
`audit-output.json`. `git diff --check` passed, and both frozen runtime source
files remain byte-identical to `origin/main`.
