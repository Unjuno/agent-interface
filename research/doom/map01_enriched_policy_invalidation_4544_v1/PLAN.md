# #4544 — enriched policy-invalidation receipt translation

## Scope

Local deterministic construction gate for the STOP in #4536. It generates the
receipt by calling the repository's current `ObservableSignalPolicyMonitor`
and uses its actual top-level timing/envelope fields and complete outcome.
The monitor clock is fixed only in the test harness so retained synthetic
clock calibration values are comparable. Receipt tests use no game, model,
task input, network, or GPU. A separate zero-model local preflight starts a
spectator MAP01 session and exercises only observe/release, with runtime
network disabled and no GPU.

## H / T / D / C / U

**H** — A required-fields-subset translator that preserves the complete
production monitor envelope and translates only host `outcome_evaluated_ns`
with a latest-possible same-session offset can retain explicit provenance and
let final admission reject a stale answer without granting input authority.
This tests the monitor/admission contract; it does not assume the helper caused
#4536's STOP (the later #4552 audit found the merged helper already accepts
additional fields).

**T** — `test_receipt_translation.py` obtains an actual event from
`ObservableSignalPolicyMonitor.observe()` using a deterministic extractor and
clock seam. Test field-preserving translation, the unconverted mixed-domain
exception and post-translation `REJECTED_POLICY_INVALIDATED`, future metadata,
malformed/unsafe outcomes, wrong source domain/session/probe count, stale or
future calibration, over-wide intervals, and reordered stage timestamps. Run
on the host and this PC's local `linux/amd64` ViZDoom image with network
disabled and the checkout mounted read-only. Then run the adapter with
`--iterations 0` to verify actual MAP01 startup and an observe-only
submit/terminal/empty physical release, with zero planner turns.

**D** — Scoped construction PASS only when every frozen offline case passes;
full raw monitor and outcome fields survive; calibration is exactly three
retained same-session probes whose recorded send/runtime/receive values
recompute the declared bounds, with uncertainty <=1 second and age <=5 seconds; only the
outcome boundary is translated; the mixed-domain witness fails before
translation; final admission after translation is
`REJECTED_POLICY_INVALIDATED`, has no executor admission, and grants no input
authority. Every retained host-stage timestamp remains labeled host-domain;
only the outcome boundary is translated and labeled runtime-domain. Any
missing semantic field or invalid calibration must fail closed.

**C** — The invalidation timestamp and clock values used in the admission
ordering test are synthetic controls based on retained #4536 iteration-8
values; they do not reconstruct #4536's missing receipt or prove historical
causality. The zero-model preflight proves startup, host/container clock probes,
read-only source mount, and a real observe-only empty release; it does not
exercise receipt translation end-to-end, any model inference, input command, or
gameplay outcome. No GPU was used.

**U** — It remains unknown whether the converter is reached correctly by a
real monitor invalidation, permits a later fresh planner turn and complete
horizon, or resolves the suspected predecessor cause. Before a formal
allocation: inspect all current issue/PR/branch/path claims; retain and audit
the generated adapter source; freeze fresh source, container/WAD hashes, seed,
output path, command and STOP rules in #4544; then consume at most one run with
no retry. The local image is currently 1.14 GB; minimize it only if
dependencies can be removed without changing the verified runtime contract.
