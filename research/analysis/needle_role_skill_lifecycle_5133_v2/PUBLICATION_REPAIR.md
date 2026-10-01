# Append-only publication repair — 2026-10-01

This repair does not change `FREEZE.json`, the consumed allocation, its source
code, formal raw, original audit, or corrected raw-only audit. It proposes a
cross-platform checkout repair and records the public sample-count correction.

## H / T / D / C / U

**H.** Preserving the three remaining text files as exact Git bytes across
Windows and Linux checkouts will let the existing frozen source/reference
SHA-256 construction gate pass on both platforms. Explicit sample counts will
then describe the retained 15-block raw correctly.

**T.** Add path-scoped `-text` rules for the two referenced source files. Keep
the original README, FREEZE, and every measured source byte-for-byte
immutable: since README is itself in the frozen source set, record its count
correction here rather than editing it. The corrected denominator is 1,000
predictions per arm per block, 15,000 per arm, and 30,000 total. Add a
publication test that checks all
frozen source/reference hashes, the derived denominator and the immutable raw
SHA-256/size. The historical performance study is not rerun.

**D.** `PASS_PUBLICATION_BYTES_SCOPED` requires every frozen source and
reference byte hash to match, denominator arithmetic and prose to agree, and
the existing raw formal file to retain the exact SHA-256 and byte size.
Otherwise `STOP_PUBLICATION_BYTES_OR_DENOMINATOR`. This cannot upgrade,
replace, or widen the retained lifecycle timing result.

**C.** Validation is a standard-library host test plus the repository's normal
analysis-index and research-workspace checks. No Docker resource slot is
needed: no scientific or timed container invocation occurs. The small test is
also suitable for an offline Python container. Raw, original audit, and
correction report are read-only.

**U.** This validates publication-byte identity and report arithmetic only. It
does not revalidate performance, repeat the formal raw audit, establish
PyTorch/LoRA/online-adaptation quality, or establish runtime/task/product
benefit. The existing scoped raw-only corrected audit remains the timing
decision source.

## Preserved evidence and observed trigger

- Base: main `d522a44d247bbdb33ed25ae66a2ed650de3e8e80`.
- Original freeze SHA-256: `2a9b6e327a02e67f5e9b7d4bce42515a69157b47ecdaac1fb1a04f085fd9f118`.
- Immutable formal raw SHA-256: `9e9a0ef349a08f69d01b7e97756b3e02d6691e835c024380f1b8da876524ab65` (316,541 bytes).
- Corrected audit report remains `results/audit-correction-04/correction.json`, SHA-256
  `PASS_CORRECTED_RAW_REAUDIT_SCOPED`; the historical `audit-04/audit.json`
  remains unmodified.
- The previous Windows-host construction run on current main passed 6/7; it
  stopped on `README.md` before reaching the reference files. Separately,
  current Git blobs for `lifecycle.py` and `loader.py` had SHA-256 values
  `e45a6b1ec6ad4995533c59d3ae560b9a91e2d31b2d7186c1cae5705f90602b80` and
  `5ff6df91ea3929f68fe77ccd6156bdb1310d0fec86088489d8b99905a7c5854f`, while
  the immutable freeze requires `c03d07dd8b2b75e061609b72ceb9f258468a422bbf2d225acf4661e6d4f23282`
  and `61c4439b3e1ee5ea19ba84b155043218a0bbd9ddaacc2ebf2338c1f046dbf863`.

This addendum records a newly prepared repair candidate. No acceptance claim
is made until the new byte test, the original construction suite, and CI pass
on the GitHub PR head from a clean checkout.
