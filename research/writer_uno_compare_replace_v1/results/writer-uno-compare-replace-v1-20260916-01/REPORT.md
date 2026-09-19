# Writer UNO compare-replace v1 — retained first result

**Result ID:** `writer-uno-compare-replace-v1-20260916-01`  
**Source/plan freeze:** `5c7eca118ac85f13ce238e577ce7aaad3bb56410`

## Disposition

**PASS_SCOPED_APPLICATION_COMPARE_REPLACE / RETAIN_SINGLE_RPC_PRECONDITION_MUTATION / HOLD_GENERAL_ATOMICITY_PROMOTION**.

Four fresh private Xvfb/Openbox/LibreOffice Writer blocks ran once each. Every operation helper used an independent `/usr/bin/python3` UNO connection. The experiment compares a stale two-RPC `read -> unconditional set` baseline against one exact-regex `XReplaceable.replaceAll(^book$ -> bookkeeperoffice)` call while another client appends `x`.

| condition | n | retained outcome |
|---|---:|---|
| baseline gap | 4 | completed append lost 4/4; final `bookkeeperoffice` |
| append then replace | 4 | replace count 0; final `bookx` 4/4 |
| replace then append | 4 | replace count 1; final `bookkeeperofficex` 4/4 |
| simultaneous race | 4 | serial outcome only; `bookkeeperofficex` 4/4 |
| candidate delayed race | 4 | serial outcome only; `bookx` 4/4 |
| append delayed race | 4 | serial outcome only; `bookkeeperofficex` 4/4 |
| stale RuntimeUID | 4 | refusal 4/4; final `book` |

Candidate trial count is 20. Unsafe/hybrid/completed-append-loss candidate outcomes: **0/20**.

## Main discriminator

The baseline reads `book`, then waits until a separate UNO append call has completed and the document is `bookx`, then performs its stale unconditional set to `bookkeeperoffice`. Exact receipts confirm `append.call_end_ns < baseline.set.call_start_ns` in all four blocks. The completed competing update is lost in all four baseline trials.

The one-call candidate keeps the condition inside Writer's replace operation. If append completes first, `^book$` no longer matches: replace count 0 and final `bookx`. If replace completes first, a later append yields `bookkeeperofficex`. Both serial orders were established deterministically in all four blocks. The 12 barrier races produced only those same two serializable outcomes.

Development also showed that a client-side 10 ms delay does **not** prove UNO server execution order. Formal race classification therefore does not infer order from client delay or timestamps; timestamps are used only in the deterministic completed-before-call arms.

## Identity guard

Each candidate call resolves an exact document URL and may require the expected Writer `RuntimeUID`. In all four stale-UID arms, the document was closed/reopened at the same URL, the old UID was refused, and text remained `book`.

## What this proves / does not prove

This provides scoped evidence that Writer's exact-regex `replaceAll` call can combine this fixture's text precondition and mutation strongly enough to avoid the demonstrated stale two-RPC lost update, including the controlled competing-append races.

It does **not** establish a documented general UNO transaction or linearizability guarantee. `replaceAll` searches a document container and may affect multiple matches outside this one-paragraph fixture. A later mutation may still change the final state. This is a distinct application-side `application_replace` capability, not OS `input.text`, and does not replace X11/IME/clipboard semantics.

## Controls

- source readback: 9/9 exact Git blobs before formal execution;
- deterministic unit tests: 6/6 PASS;
- formal blocks: 4/4 PASS, 28 rows total;
- baseline completed-append-lost: 4/4;
- candidate unsafe outcomes: 0/20;
- stale UID refusals: 4/4;
- formal reruns: 0;
- model/provider/network calls: 0.

## H/T/D/C/U

**H:** one exact Writer `replaceAll` RPC avoids a concrete stale-check/set lost-update window for this document shape.  
**T:** four source-frozen fresh blocks; deterministic both-order arms plus three barrier races and stale identity control; fresh third-client final readback.  
**D:** scoped PASS because baseline loses a completed append 4/4 while candidate preserves one of the two serial orders in 20/20 and rejects stale UID 4/4.  
**C:** Writer regex/search scope and UNO request processing are implementation-specific; operations after the call remain possible.  
**U:** one Writer paragraph/host/version; no general atomicity, durable save, OS-input equivalence, other apps/platforms, model/token claim.

## Successor

Treat this as a separate application-side delivery route. Before shared-interface promotion, test exact replacement scope on multi-paragraph/multi-match documents and prove that a route advertises its semantic blast radius. For the X11 route, keep the independent server-grab/post-input verification work separate.
