# Cancellation-callback exception receipt boundary

Status: frozen synthetic construction probe. This is a regression investigation
for #57's requirement to retain completed effects and typed partial outcomes.

## H / T / D / C / U

**H.** If the required cancellation callback raises after the first side effect
has completed and released input, the compiled adapter may propagate the
exception instead of returning a receipt that preserves the completed prefix.

**T.** Run the exact adapter and compiled-core source from PR #7443 head
`6144a1b0a2c88f5d88ff1fce148381f1f22269e`. Use its pinned synthetic Chromium
frame `frame-068.png`, a deterministic fake checked client that records one
completed action with verified empty release, and a callback that returns
`False` for the first three checks then raises on the fourth (the next loop
check after that action). Make one invocation, no retries. No GUI, game,
Docker, model/provider call, or task allocation.

**D.** PASS only if the adapter returns a typed receipt preserving the one
completed transition and its release, with no second action. FAIL if the
callback exception escapes or the receipt omits the completed prefix. A result
that calls the event `cancelled` without distinguishing callback failure is
reported separately and is not treated as infrastructure diagnosis.

**C.** This probes an adapter-contract exception after an already completed
action. It does not test cancellation timing, real client callbacks, GUI input,
live Mindustry transfer, or the three-arm economics result. The test uses a
synthetic client and a retained Chromium fixture image.

**U.** This is one exact-head construction result. It identifies behavior in
the tested source revision only and does not establish frequency or product
impact.

## Frozen source

The archive under `sources/` is copied byte-for-byte from the PR head above.
`FREEZE.json` pins the PR commit, source blob IDs, SHA-256 digests, fixture image
digest, callback sequence, and expected gate. The run occurs after this freeze
is committed.
