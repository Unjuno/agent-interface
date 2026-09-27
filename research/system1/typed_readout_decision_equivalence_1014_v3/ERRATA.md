# Hash correction: line-ending encodings

The earlier draft of this note incorrectly called the merged #4639 README corpus hash an upstream metadata error. Git object inspection shows that the README value `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd` is the correct SHA-256 for the canonical LF Git blob (270,228 bytes).

The predecessor source manifest's `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c` is the SHA-256 of its Windows CRLF worktree form (270,292 bytes), which was the exact corpus input consumed by this successor's frozen GPU run. The two byte streams are related by LF-to-CRLF conversion; JSONL records are identical. The frozen runner therefore correctly checks the tested Windows byte stream, but a clean Linux checkout lacked those bytes until this successor added `corpus_source/corpus.jsonl`.

This is a provenance/reproducibility clarification only. No prior raw evidence or formal result has been changed and no formal run has been repeated.
