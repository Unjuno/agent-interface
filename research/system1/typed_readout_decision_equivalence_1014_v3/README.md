# Full-corpus typed decision equivalence — Issue #4652

This is a new categorical-decision allocation after the separate full-vocabulary
and selected-score construction STOPs in #4623 and #4639. It measures whether
the eight answer-token winners differ over every question in the unchanged
64-bundle × 16-slot corpus. It neither relaxes nor revises either predecessor's
score gate.

The frozen local model, full weight digest, license, corpus, and original CUDA
image are retained under
[`../typed_readout_prefix_gpu_1014_v1/`](../typed_readout_prefix_gpu_1014_v1/).
This package keeps only its own protocol, execution sources, and new outcome.

The formal GPU run consumed the predecessor corpus in its Windows CRLF worktree
form: 270,292 bytes, SHA-256
`85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`. Those exact
bytes are retained at [`corpus_source/corpus.jsonl`](corpus_source/corpus.jsonl).
The canonical LF Git blob is 270,228 bytes with SHA-256
`c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`; converting
its line endings to CRLF reconstructs the tested bytes exactly. The earlier
erratum incorrectly described the canonical Git hash as wrong; see
[`ERRATA.md`](ERRATA.md) and [`CORPUS_REPRODUCTION.md`](CORPUS_REPRODUCTION.md).
Neither predecessor raw evidence nor this formal result has been rewritten.
No semantic quality, task correctness, GUI behavior, authority, runtime,
cross-model portability, or cache speedup claim follows from a categorical
agreement result.
