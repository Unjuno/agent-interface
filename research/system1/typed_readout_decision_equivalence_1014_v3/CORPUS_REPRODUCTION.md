# Corpus byte reproduction note

The formal run consumed the Windows worktree byte stream of the predecessor corpus:
270,292 bytes, SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`.
That exact byte stream is retained at `corpus_source/corpus.jsonl` and is what the frozen runner expects.

Git stores the predecessor `corpus.jsonl` as LF bytes: 270,228 bytes, SHA-256
`c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`.
Replacing each LF byte in that Git blob with CRLF reconstructs the retained run input byte-for-byte.
The JSONL records are unchanged; these are two line-ending encodings of the same corpus.

The frozen formal code, freeze, results, and previous commits are not rewritten. This additive file resolves clean-checkout reproduction of the exact input bytes without claiming a second formal run.
