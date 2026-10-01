# Explicit guarded activation: integration and primary self-use

The primary agent personally recovered a one-time loss of target focus using
the new public MCP `interface_guarded_activate_window` and the existing explicit
window review. Independent app events after public close show **A received
exactly z; unrelated B received no key**. This is one bounded GUI case; candidate
adoption remains **HOLD**, and the strict primary caller's STOP policy is unchanged.

The ordinary `window.activate` implementation already exists with retained live
evidence. This integration exposes it on the guarded Python/MCP path with exact
registered window ID, current observation sequence, binding revision, explicit
caller expiry and timeout. It uses core admission. Foreign IDs/stale sources/
revisions and uncertain cleanup refuse before dispatch. Success or uncertainty
blocks editing until explicit window review. Core refusal preserves a pre-existing
review requirement. No automatic refocus, input replay, alias renewal, background
sensor, new authority or semantic success assertion is introduced.

## Personally selected public-tool sequence

Trial source: `8be49d281101a430ec728412fe526201ff919b0f`.
PLAN hashes were recorded before launching the private Xvfb/Openbox/Tk fixture;
the zipapp and host bundle are built from that exact committed source.

1. Observe and review A/B screen; explicitly ground A's entry.
2. Click A, wait 250 ms, then request z. App moves focus to B after 40 ms.
   The focus guard stops at text op 5; the original returned image shows B active
   and both entries empty. Release is verified neutral.
3. After reviewing that image, sample the execution clock and explicitly activate
   registered A, using the returned source sequence 6, revision 0 and a 5 s expiry.
   Activation returns no image/text input; its WM receipt is not visual confirmation.
4. Explicitly review A. The primary reviews its image; revision advances to 1
   and old aliases are revoked. Ground a new alias from source 7.
5. Choose a new click/text program. The returned image shows z in A, empty B.
   Review it, public-close, acknowledge the neutral release, and close transport.
6. Only afterward read the independent app key-event oracle.

The trial uses the **generic instrumented public MCP host**, not
`createPrimaryCaller`. Its predeclared rule permits this specific focus failure
only after neutral release and image review; other input/transport/presentation
failures mean close with no retry. No STOP is cleared or bypassed in an older
frozen trial. The new activation tool does not override callers' STOP policies.

Retained primary counts: **9 public calls, 4 original images reviewed, 8 XTEST
input emissions**. Activation itself has zero XTEST emissions but changes WM
focus and is still an effect. All images are reviewed before the next effectful
stage. Original PNGs equal their response image bytes; no presentation fallback
was needed. Public close and transport exit are verified. Fixture children exit
`[0,0,-15]`; this is terminal owned-process cleanup, not all-zero success.

Recovery reply-3 to reply-8 spans **51,618.63 ms on the host clock**. Overall
first-send to final-reply is 93,347.62 ms: request-outstanding 2,089.47 ms,
presentation callbacks 15.02 ms, other host intervals 91,243.13 ms. These are
host boundaries including orchestration/caller gaps, **not** isolated reasoning,
first useful model feedback or semantic completion latency. This result does not
establish human tempo or a matched speedup. Provider tokens/cost remain unmeasured.

## Program-driven construction and retained failures

`construction/live-01` failed exposure/setup: Openbox frame identity and fixed
coordinates were incorrectly reused from the earlier no-WM fixture. The intended
click did not arm the disturbance; two A key events occurred, and activation
refused because its target was not a managed client. **This is not recovery PASS.**
The original outputs and source snapshots remain unchanged.

`construction/live-02` is a separately frozen successor: select the managed Tk
client from the content-window parent and use entry coordinates from fixture
readiness. Initial guard stops; explicit activation completes; editing before
review refuses; old alias after review refuses; new grounding/input yields A=z,
B empty. It is program-driven construction, distinct from primary image judgment.

Two native suite invocations fail and are retained: new public discovery was
absent from the legacy parity expectations, then the runtime additive tool failed
the old exact parity comparison. The legacy research relay allowlist stays
unchanged; expectations explicitly allow the additive public tool and the runtime
relay permits it. The third complete invocation passes **341 protocol +156
harness tests**. New bridge tests initially fail because activation is absent;
the MCP test initially fails on unknown tool. A further test exposed accidental
clearing of an earlier review block after core refusal; repaired before live runs.
Activation tests also pass under Python -O.

## Raw-only verification

The archive retains 297 files, including all original primary exchanges,
construction failures, three native logs/results, source snapshots and frozen
plans. All member hashes are reread from tar. Wrong-target event mutations reject
at the independent-effect semantic check in normal Python and Python -O.

```sh
python3 runtime/results/guarded-activation-01/verify.py
python3 -O runtime/results/guarded-activation-01/verify.py
```

The verifier freshly extracts evidence and never invokes GUI/input. The original
core lease checks and WM polling limits still apply. Already-held input,
within-target editing focus, transport blocking, query-to-input races, DOOM live
threat effects, general recovery coverage and candidate-wide adoption remain
unproved. This does not close Issue #59.
