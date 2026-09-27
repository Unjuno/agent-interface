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

The authoritative predecessor `SOURCE_MANIFEST.json` and direct file hash bind
`corpus.jsonl` to SHA-256
`85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`. A
different corpus hash in the merged #4639 README is an upstream metadata
discrepancy; it has been recorded on both Issues without rewriting either
predecessor's raw evidence.

No semantic quality, task correctness, GUI behavior, authority, runtime,
cross-model portability, or cache speedup claim follows from a categorical
agreement result.
