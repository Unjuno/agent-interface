# Issue #2928 — current caller session-context boundary probe

## H/T/D/C/U

**H.** The current-main acquisition caller requires a request `session_id` in
its reuse spec, but may omit it from the payload sent to the reuse and final
revalidation adapters. If so, session binding depends on adapter closure state
that is not explicit in the caller payload contract.

**T.** Freeze and invoke the exact main caller source once per two shadow cases:
current cached session and prior cached session, both under request session
`session-current`. Record the payloads received by reuse/final revalidation and
whether the execute adapter is reached. Use deterministic adapters and a
zero-action `safe_yield` execute stub. No Docker, provider, model, GUI, input,
network, or runtime write.

**D.** `HOLD_SESSION_BINDING_DEPENDS_ON_ADAPTER` if current request session is
not explicitly present in either revalidation payload. This records an
interface boundary only, not actual stale-cache acceptance or a production
safety defect.

**C.** Adapters may close over current session context. The execute adapter is
shadow-only and returns `safe_yield` with zero completed actions. A separate
raw-only auditor imports neither subject nor runner.

**U.** Two synthetic cases, one Windows host, Python 3.12.10, and one caller
source snapshot. No real adapter, cache lifecycle, GUI/task effect, latency,
security or product claim.

## Result

The source blob and SHA-256 matched the freeze. Both rows were reconstructed by
the separate auditor with `errors=[]`. In the stale case, request session was
`session-current` and cached target session was `session-prior`; both
`reuse_revalidate` and `final_revalidate` received only the cached target
object, without the current request session. Both paths returned the adapter's
`revalidated` decision and the caller reached the shadow execute adapter; the
stub returned `safe_yield`, zero completed actions, and no effect.

Disposition: `HOLD_SESSION_BINDING_DEPENDS_ON_ADAPTER`. The caller's current
session is not explicit at either adapter call boundary, but an adapter could
hold it in closure state. This does not establish that any configured adapter
accepts stale targets. A useful next step requires the real adapter construction
site or a contract requiring an explicit current-session binding receipt.

The local run was host-only because no Docker slot was assigned to this lane;
the shared slot had been explicitly assigned to #5133. No container was
started, inspected, or changed by this probe.

Post-run construction checks: `py_compile` passed for the probe/auditor/control
scripts; the auditor accepted the retained raw row set and rejected 5/5 copied
mutations (missing row, duplicate row, changed request session, altered target
payload, and altered execute count). These controls re-invoke only the auditor
on temporary copies; they do not re-run the caller or scientific rows.

## Reproduction

From the repository root, point `probe.py` to the exact frozen main source and
an absent output path, then run the independent audit separately:

```powershell
python scratch/2928-session-binding-probe/probe.py work/arena-v1-owner-read/research/live_control/adaptive_acquisition_caller_v3.py scratch/2928-session-binding-probe/RAW.json
python scratch/2928-session-binding-probe/audit.py scratch/2928-session-binding-probe/RAW.json
```

The `work/...` path is local-only; in a complete repository checkout, use
`research/live_control/adaptive_acquisition_caller_v3.py` from the same frozen
main SHA. The formal scientific allocation count is zero.
