# Issue #59 — composed health/ammo cover guard (A02 construction test)

## H / T / D / C / U

**H.** Composing two existing typed `ObservableSignalGuard` instances—health floor and positive-ammo floor—can close the A01 monitor gap without changing input authority: a fire-containing cover remains valid at ammo=1 but requests a new decision on ammo=0, unknown/stale ammo, or observation-binding mismatch.

**T.** Freeze current-main source `observable_signal_guard_v2.py`, a deterministic source state (health=100, ammo=4, common sequence/capture/binding), and seven typed counterfactual observations. The probe instantiates two guards from the frozen generic class and treats any non-UNCHANGED/non-SOFT outcome from either signal as a request to invalidate existing cover. No Doom controller, model, game, GUI, OS input, or product source is modified or launched.

**D.** Pass this construction gate only if (1) valid ammo=1 and unchanged positive health preserve cover, and (2) ammo=0, unavailable ammo, non-advancing ammo sequence, mismatched ammo binding, and health below its floor all fail closed. The independent auditor must reconstruct every expected outcome from the frozen input and pass all seven cases. Otherwise retain a FAIL/STOP.

**C.** Two independent guards may disagree on event epochs, create excessive interruptions, or be wired incorrectly in the real controller. This test proves only the minimal compositional semantics, not runtime cancellation, release latency, useful firing, survival, or benefit.

**U.** Construction-only prototype, not integrated v39 behavior and not a live allocation. A PASS would justify implementation/regression review, not a live run. A live successor requires a separately assigned lane, exact current-main freeze, and retained invalidation/cancel/verified-empty-release timing.

## Runtime

OrbStack's read-only image inventory already failed in A01 on an inaccessible cached containerd blob (`operation not supported`). To avoid repeating an infrastructure probe or pulling/building an image for this stdlib-only semantic test, A02 used CPython 3.14.5 on host macOS arm64; no isolation/resource enforcement is claimed.
