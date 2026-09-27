# #2802 allocation 02 — live X11 ordered-event contract transfer

## Decision

**PASS_X11_TIMESTAMP_ORDER_BOUNDARY_SCOPED**. One fresh allocation completed 24/24 cases in four prospectively frozen six-case batches; formal reruns/replacements/tuning 0/0/0. The predecessor allocation01 remains immutable STOP_CASE and is not pooled.

## Result

- AB_BURST ties: **4/4**
- BA_BURST ties: **4/4**
- BAB_BURST ties: **4/4**
- retained selected events: **72 per observed policy stream**; two X connections agree on every case
- co-timestamp comparator: **12 false ordered-prefix satisfactions across 8 cases**
- strict-time comparator: differs from ordered semantics in **8 cases**
- sequence-aware candidate: **0 independent prefix mismatches**
- independent raw audit: errors=[]
- corruption controls: **12/12 rejected**
- every actor/policy/case/Xvfb exit and cleanup gate: PASS

The result does not falsify #1764. #1764 intentionally defines same-timestamp event-family fragments as unordered co-occurrence. This allocation proves only that such semantics cannot be silently reused for a contract whose meaning is *later B event after A*. Conversely, requiring a strictly greater timestamp loses valid A-before-B events that share a server millisecond.

## H / T / D / C / U

**H:** Same-timestamp co-occurrence, strictly increasing timestamp order, and observed channel order are distinct contracts on a live X11 event stream. Preserving a local ordinal can implement the latter without changing the first-A source-tick deadline.

**T:** Scientific sources are byte-identical to allocation01. Same six scenarios x four cyclic repetitions, same private Xvfb/actor/two-observer PropertyNotify path, 80ms source allowance, 10ms SPACED controls, 120ms H request, exact raw 32-byte packets, and same independent audit gates. Only execution serialization changed to four immutable six-case batches after excluded construction showed the old 28s/24-case envelope was infeasible.

**D:** All inherited complete-denominator/source/process/packet/cleanup/oracle/tie/discriminator/corruption gates pass.

**C:** Burst scheduling is a directed exposure, not a natural tie-rate estimate. Local watcher order is not a cross-client total order and does not prove causality. A complete local ordinal also assumes no unobserved event loss.

**U:** Private software X11 only; no real-application semantic completion, reconnect/wrap, multi-writer order, model utility, task success, latency/token benefit, production runtime or cross-platform claim. Timing is diagnostic only.

## Execution repair, not scientific tuning

Allocation01's first three complete cases each took about 2.84–2.94s, while its frozen whole-run budget was 28s for 24 cases; that orchestration could not support the declared denominator. Allocation02 kept all scientific bytes/gates unchanged and changed only execution serialization. Excluded construction completed 6/6 in 2.187–2.733s per case.

## Provenance

Remote preformal freeze: branch `research/issue-2802-x11-order-batches-20260922`, commitment head `82eff7fe8bb104ea8d6022c1039b3d299440f8a8`, Issue #2802 comment 5770706302. The initially uploaded FREEZE had a formatting-only byte mismatch and was corrected before formal0; current remote FREEZE Git blob `7b6882ecc1ac30d6f5d1fe5ed58413678cefc292` matches the local bytes. Freeze SHA-256 `f8a5b6f5b5e09baf5e5cf0d8392f12ac7951957c29bedf5202d1976dda5803c8`.

RUN SHA-256 `dccaf122c990ff492d5a90af6c5312db88c6776229408f110276c05de0aa07bb`. AUDIT SHA-256 `75a1e585cfbe4d81abfaa2fe1587eef17419a63d42e137202c7cb011b2acc748`. AUDIT_CONTROLS SHA-256 `b21586376aae34f245f5977fc0f04c8cefa70a77e46414b67aa9ecc167e15d25`.

## Integration meaning

A temporal contract API must name whether it means co-occurrence at a source tick, later event order on a declared complete channel, or causal application completion. These are separate evidence types. No action authority follows from this result.
