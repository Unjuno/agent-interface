# Referenced-image ACK/GC boundary v1 — formal result

Issue: #4140  
Allocation: `referenced-image-ack-gc-20260922-01`  
Disposition: **PASS_REFERENCED_IMAGE_ACK_GC_SCOPED**

## Chronology

One excluded 21-case construction matrix completed before the public freeze. A first preformal GitHub publication had two byte-level source-layout mismatches; both were detected with **formal invocations still 0**, corrected to the exact locally tested bytes, and recorded in Issue #4140. The frozen branch blobs then matched local source exactly.

Formal batch1 and batch2 each ran once, 21 fresh cases each. Reruns/replacements/pooling/post-result tuning: 0.

## Result

| policy | cases | cases with unresolved unacknowledged page | unresolved page references | blob delete events |
|---|---:|---:|---:|---:|
| DELIVERY_GC | 14 | 12 | 18 | 24 |
| ACK_PAGE_GC | 14 | 2 | 2 | 8 |
| ACK_REFCOUNT_GC | 14 | **0** | **0** | 6 |

The directed controls exposed both predicted unsafe boundaries:

- `DELIVERY_GC`: with two delivered-but-unacknowledged distinct pages, GC deleted the retained blobs and made both pages unresolvable in both repetitions.
- `ACK_PAGE_GC`: ACK of page1 in the shared-blob schedule deleted the blob still referenced by unacknowledged page2 in both repetitions.

The candidate `ACK_REFCOUNT_GC` preserved every unacknowledged page in all 14 candidate cases. For distinct blobs, valid page1 ACK deleted only page1's now-unreferenced blob and page2 remained exact. For a shared blob, page1 ACK retained the blob; final ACK through page2 removed it. Duplicate page1 ACK was idempotent. Stale-epoch and over-prefix ACKs were refused without state mutation.

Every operation receipt retained `authority=none` and `input_dispatched=false`.

## Evidence

- Formal cases: 42/42
- Batch runner exits: 0, 0
- Component worker exits: 42/42 zero
- Independent raw auditor: errors=[] / PASS
- Corruption controls: 10/10 rejected
- Source rehash after formal: 5/5 scientific source files unchanged

Raw SHA-256:
- formal-1 RAW: `e20f82167f55227c9a0fa896b967f44b9a6a08202ac68cd32ce4e56258f107ce`
- formal-2 RAW: `81b0e22ce2351ef7e733d134ecd0d27dea5c52fefcc9129072937ad350f7d766`
- formal audit: `5633c5eede3ac902957eb0373eae08286189b503a7a9d0a78ed3cfda81a6f435`
- controls: `049225450e36e58ee5a212cbae55149475279c9339b42f93a8f987f3964255e6`

Lossless evidence archive: 13,304 bytes, SHA-256 `847b6be931e9ca33c5e4d36271a9054ed0b5605453c585dd76347e372c6002c3`.

## Scope

This is a private SQLite retention-lifetime fixture. It does not establish model viewing, exactly-once delivery, hostile ACK authentication, power-loss safety, concurrent GC, a production TTL, performance benefit, GUI task correctness or product readiness. The broad repository ROADMAP remains open.
