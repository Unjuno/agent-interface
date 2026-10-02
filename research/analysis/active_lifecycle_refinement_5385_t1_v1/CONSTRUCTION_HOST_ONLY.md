# Construction record — host-only, not a formal result

The exact source candidate/auditor CLI contract was exercised once each on
Windows CPython 3.12.10 before source freeze. This record exists only to verify
serialization, command wiring and the independent raw-only audit; it is not the
preregistered Docker invocation and does not establish the experiment's
disposition.

- Unit tests: `python -B -m unittest -v test_refinement.py` — 3/3 PASS.
- Syntax: `ast.parse` over `experiment.py`, `audit.py`,
  `test_refinement.py` — 3/3 PASS.
- Candidate: one host construction invocation; exit 0; 8,407 JSONL records,
  containing 8,403 depth-four trace rows (2,801 per candidate) and four
  header/summary records.
- Raw SHA-256:
  `a0f9b8f3120aa0f74bf4a4c37c068a0e574958982347c958a91216dea408619b`.
- Lossless gzip archive: 56,990 bytes, SHA-256
  `6e9e9bedc6a9c78f2aa479e4edda341250dd04151b433d349f834d320bc33740`;
  decompression round-trip reproduced the raw SHA exactly.
- Independent auditor: one host construction invocation; exit 0;
  `PASS_BOUNDED_ALTERNATING_REFINEMENT`, 8,403 rows, zero errors, all four
  corruption controls rejected. Audit JSON SHA-256:
  `214b004655e7be2e64f0e706425080b849d4884add12a9c8f31a6000cc290d7f`.
- Construction args explicitly used `CONSTRUCTION_UNFROZEN` and
  `CONSTRUCTION_HOST_ONLY`; no formal allocation or source freeze is implied.
- No Docker/container, model, GUI, X11, input, network, GPU, or external effect
  was used in this host construction check.

The preserved construction archive and audit are separate from the future
formal `raw/formal.jsonl` and `raw/audit.json`. They must never be pooled or
relabeled as Docker evidence.
