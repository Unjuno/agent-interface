# #4871 corpus identity: line-ending forensic audit

Date: 2026-09-29 (Asia/Tokyo)

## H / T / D / C / U

- **H:** #4871's 270,228-byte current-main corpus and its frozen 270,292-byte precision-study corpus contain identical 64 JSONL records; their byte-hash mismatch is solely LF versus CRLF serialization.
- **T:** Read-only comparison of two exact files committed on main `12d15dd81c47e8af80abd3172d67d934452f36ca`: `research/system1/typed_readout_decision_equivalence_1014_v3/corpus_source/corpus.jsonl` and the immutable successor copy `research/system1/typed_readout_precision_boundary_1014_v5/corpus.jsonl`. No data was rewritten, no local GPU/container was touched, and no formal allocation or retry occurred. Docker was not feasible under the active #5085 hold; a different research container was reported active in its latest comment.
- **D:** Main-v3 bytes: 270,228; SHA-256 `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`; 64 LF separators, no CRLF. Frozen-v5 bytes: 270,292; SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`; 64 CRLF pairs. Replacing only `CRLF` with `LF` makes all bytes equal; changed normalized lines: 0; JSON records equal: 64/64. The v5 corpus file's bytes exactly match the hash frozen in #4871. An independent verifier and a one-byte non-EOL mutation control pass. The distinct #4912 v5 GPU construction already reports FP32 tolerance 9/9, FP16 and BF16 0/9; its separate raw-only audit passed 27 rows and 5/5 corruption controls (PRs #4919/#4923).
- **C:** Host-side Python 3 standard-library byte/JSONL provenance audit; no model/tokenizer load, inference, GPU/CUDA, Docker/OrbStack, or formal result. Exact inputs remain unchanged on main.
- **U:** This establishes byte/record relation only for the two named current-main paths and this commit. It does not change #4871's original `STOP_CORPUS_HASH_MISMATCH`: that one-shot required exact bytes and correctly stopped. It does not substitute #4912 v5's independent allocation for #4871, establish precision performance, or authorize a new GPU run.

## Reproduction

From the repository root:

```powershell
python research/analysis/typed_readout_corpus_eol_audit_4871_v1/reproduce.py
python research/analysis/typed_readout_corpus_eol_audit_4871_v1/verify.py
python -m unittest discover -s research/analysis/typed_readout_corpus_eol_audit_4871_v1 -p 'test_*.py' -v
```

Machine-readable reproduction and independent receipt are retained as `result.json` and `audit.json`. The original #4871 STOP and #4912 v5 result remain immutable.

## Preserved launcher failure

The first host invocation attempted to read the two paths from the sparse worktree and stopped with `FileNotFoundError` before loading either input. The worktree included only the Qwen package. This was a checkout-layout error, not corpus evidence. The reproduction and independent verifier were changed to read exact Git blobs from the frozen commit directly; the first failure is retained in `launcher-stop.json`.

The first staging attempt also refused this new `research/analysis/` path because the worktree sparse specification includes only the Qwen package. The index remained unchanged. The exact staging diagnostic is retained in `git-stage-stop.json`; publication uses `git add --sparse` for the explicitly scoped evidence directory.
