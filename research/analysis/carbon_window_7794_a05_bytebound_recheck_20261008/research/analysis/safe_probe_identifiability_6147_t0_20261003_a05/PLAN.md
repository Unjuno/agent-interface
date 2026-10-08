# Issue #6147 T0 A05 — two-probe non-identifying convergence

Fresh allocation `AI-6147-T0-20261003-05`, narrowly addressing the exact
convergence control specified in Issue comment #5936962860. A03/A04 outcomes
remain untouched and their RAW files are not reused. Main base:
`43f7cd88d91af05036fae2100ec4e155c59e105c`. Host CPython, standard library
only; no container/OrbStack/model/GPU/GUI/network/physical input.

## H / T / D / C / U

**H.** For two initially aliased, action-different candidate states C0/D0, the
fixed safe sequence `p→q` can leave the initial identity unresolved (identical
observable output trace) while converging the machine to one current terminal
state Z whose declared effect envelope is the same safe action in every
reachable terminal world. The sequence must not be credited as identifying
the initial state.

**T.** Freeze a deterministic Moore machine where `p` maps C0/D0 to distinct
intermediate C1/D1, `q` maps both to Z, all these observations are READY, and
initial/intermediate action envelopes differ. Enumerate every safe
output-contingent tree through depth 2, retain terminal reachable-state and
effect sets, compare all fixed safe words through depth 2, and independently
audit that the selected p→q history has one current terminal state/effect but
no initial-state identity. Explicitly reject mutations for unsafe `u`, missing
output branch, initial identity leakage, stale/noncurrent terminal effect,
fabricated convergence, and same-image recapture as identification. One
candidate invocation followed by one independent raw-only auditor invocation;
no retries/tuning.

**D.** `PASS_METHOD_SCOPED` only if all tree sets/counts/digests and optimum
match the independent auditor; the unique depth-two selected convergent policy
is p→q; every safe word through depth 2 has the same observation trace from
C0/D0; the terminal belief is exactly `{Z}` with only the declared current
effect envelope; initial identity remains false; and every injected mutation
is rejected. Any mismatch or missing coverage is FAIL/STOP.

**C.** A real model may not include the true state or transition; typed current
effect receipts or ordinary YIELD may be safer. Convergence is only useful if
the model's terminal envelope is independently trustworthy.

**U.** One finite deterministic authored machine only. This is not a real-GUI
probe-safety, state-completeness, effect-truth, authority, runtime, product, or
cross-domain result. It does not close the broader #6147 T0 or authorize T1.
