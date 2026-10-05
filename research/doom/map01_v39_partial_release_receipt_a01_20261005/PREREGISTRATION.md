# V39 partial per-key release receipt A01

## H / T / D / C / U

**H.** The current #7847 owner candidate loses an already confirmed per-key
`CONFIRMED_PHYSICAL_UP` measurement if a later held-key release raises before
the aggregate `owner_release` record is appended. A bounded partial record
should preserve completed rows, remain aggregate-unverified, fail the owner
closed, and retain the original exception.

**T.** Use the exact #7847 candidate owner and its existing V12 fake-display
integration harness. Admit F8 and F9 with distinct step contexts; inject an
exception on the second cleanup `KeyRelease`; inspect the owner record, bridge
emissions, fake key state, and whether a later down is rejected. Run the test
once against the pinned candidate baseline (RED), then once against the
versioned candidate repair (GREEN). No GUI, game, model, OS input, or live
allocation is in scope.

**D.** RED is the expected loss: no `owner_release` record and no F8 release
measurement despite F8 being physically up. GREEN requires one unverified
partial `owner_release` with exactly the context-bound F8 receipt, one bridge
release row, F9 still explicitly held in fake state, and no subsequent input
injection after the owner faults. The original injected exception must
propagate.

**C.** This is a deterministic exception-ordering construction test. It does
not establish X11 failure frequency or real input state. The fake display
does not model application consumption, useful feedback, recovery, or game
behavior.

**U.** One two-key fake-display schedule only. It cannot satisfy the separately
gated #59 live requirements for threat exposure, independently useful live
feedback, bounded recovery, a separately identified MAP01 attempt, or matched
performance.
