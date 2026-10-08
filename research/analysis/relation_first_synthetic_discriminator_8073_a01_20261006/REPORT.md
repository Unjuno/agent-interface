# #8073 synthetic relation-first retrieval discriminator — A01

**Disposition: PASS_SYNTHETIC_RETRIEVAL_DISCRIMINATOR_SCOPED**

This is a bounded synthetic pipeline-sensitivity result. It is **not** the full Issue #8073 method comparison and must never be reported as `PASS_METHOD_SCOPED`, evidence that relation-first literature search is better, or evidence that any retrieved research idea is valid.

## H / T / D / C / U

- **H:** on a deliberately frozen corpus containing low-lexical/high-relational positives and high-lexical/low-relational decoys, exact relation-edge retrieval should recover the seeded positives while exact keyword-overlap retrieval preferentially surfaces the decoys.
- **T:** 8 target cards, 24 source cards, top-3 exact-Jaccard retrieval. Compare keyword tokens with relation-edge strings. Candidate once, independent raw-only auditor once, ten copied-output mutations. No external search/model/GUI/network.
- **D:** scoped PASS only if relation-first retrieves 8/8 seeded positives, keyword-first 0/8, relation valid yield exceeds keyword valid yield, relation decoys are fewer, authority remains false, audit has zero errors, and 10/10 controls reject.
- **C:** the corpus was intentionally authored to contain the hypothesized discriminator. This tests whether the proposed measurement pipeline can see that discriminator, not whether the discriminator occurs in real literature retrieval.
- **U:** real search engines, source-corpus coverage, equal query/time budgets, blinded assessment, reviewer agreement, repository novelty, source validity, candidate testability and research productivity remain untested.

## Construction / freeze integrity

C01 failed before formal because three supposed low-lexical positives still shared target surface terms, so keyword-first retrieved 3 seeded positives instead of the planned 0. C02 changed only those positive surface keyword lists and passed construction.

The first remote freeze attempt then exposed a controls-path defect: construction `test_controls.py` hard-coded `result.json`. No formal invocation had occurred. `PREFREEZE_CORRECTION.md` preserves this and `test_controls_v2.py` only parameterizes result/output paths.

One convenience readable `corpus.json` upload was serialized differently from the authoritative source bytes. Formal execution therefore used a fresh restoration of the exact Git-published `SOURCE_V2.tar.xz.b64` capsule, not that convenience serialization.

Authoritative capsule Git blob: `c42a9a8b884bb1c42616313809808ea3a89eea84`.
Decoded XZ SHA-256: `85d9374fce8b9f536f817e8eaabc1bcfb39993a9320d1a9ae9081a4874d27462`.
Expanded tar SHA-256: `c16be6fbd45d4764c5fa7a9ecdf002efc8641692af1a08eca82c77bd93149927`.
All 9 restored member hashes/sizes matched before formal.

## Formal first outcome

- keyword-first: seeded positives **0/8**, valid hits **0**, high-lex/low-rel decoy appearances **13**
- relation-first: seeded positives **8/8**, valid hits **8**, high-lex/low-rel decoy appearances **8**
- independent audit: **78 checks, errors=[]**
- copied-output controls: **10/10 rejected**
- authority grants: **0**
- candidate/auditor/control invocations: **1/1/1**
- reruns/replacements/tuning after freeze: **0**

Formal raw SHA-256: `33155da3471450c7b4a363825904e945b652ab505991598b4116288750bbc8c1`.
Audit SHA-256: `a081fe8772727287e58bcb08b6a1056813a31b2735eeee7796401126c0a51fbd`.
Controls SHA-256: `d8f25c4c2b8d2d6ca9580eef8cf07d8c94f60cb63f5a0f1a09c62b2a7be1f0e8`.

The enclosing execution surface returned status 1 only after all three frozen scientific commands returned 0 and the evidence was retained. This outer harness anomaly is preserved and does not trigger a scientific rerun.

## Scope / next rung

The meaningful next #8073 allocation remains the original proposal: a fixed real source corpus, equal search/query budget, relation-first vs keyword-first retrieval, deduplication, blinded independent rating of validity/nonduplication/testability, seeded controls, and an independent effort/blinding audit. This synthetic result only shows that such a pipeline can discriminate the deliberately constructed low-lex/high-relation vs high-lex/low-relation pattern.
