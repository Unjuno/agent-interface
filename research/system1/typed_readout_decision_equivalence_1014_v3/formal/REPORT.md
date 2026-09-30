# Full-corpus typed decision result — Issue #4652

**Disposition:** `PASS_TYPED_DECISION_EQUIVALENCE_1024` on the frozen synthetic
corpus. This is a decision-equivalence result only; it does not repair, pool, or
relabel #4623's full-vocabulary score STOP or #4639's selected-score STOP.

## H / T / D / C / U

- **H:** full-prefill and shared-prefix-cache execution choose the same winner
  among token IDs 15–22 for every question in the 64×16 corpus.
- **T:** one local, network-disabled Docker run on the NVIDIA RTX 3080 Laptop
  GPU, using the frozen Qwen2.5-0.5B-Instruct revision, FP16, exact corpus and
  cache helper. All 1,024 bundle/slot pairs retained both eight-score vectors,
  winner IDs, margins, prefix hashes and descriptive call timing.
- **D:** one formal invocation, exit 0; 1,024/1,024 categorical winners matched;
  zero mismatches. An independent implementation in a separate GPU container
  reconstructed all 1,024 pairs, exit 0, `errors=[]`, zero winner mismatches.
  The frozen PASS gate is met.
- **C:** only full-prefill versus shared-prefix-cache execution differs. Model,
  inputs, token IDs, dtype, order and device are held fixed. No absolute/relative
  score tolerance or timing gate was applied in this categorical-only successor.
- **U:** one synthetic corpus, checkpoint, software image and GPU. Agreement
  does not establish that either answer is semantically correct, useful on real
  applications, safe to execute, or faster. No runtime, GUI, product, or
  cross-device claim follows.

## Raw outcome

- Model revision: `7ae557604adf67be50417f59c2c2f167def9a775`.
- Model weight SHA-256:
  `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Consumed corpus bytes: 270,292-byte Windows CRLF form, SHA-256:
  `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`, retained at `corpus_source/corpus.jsonl`.
  The canonical LF Git blob is 270,228 bytes with SHA-256
  `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`; LF-to-CRLF
  conversion reproduces the exact input.
- Formal: `FORMAL_001.json`; exit code `0`; paired rows `1024`; mismatches `0`.
- Independent audit: `AUDIT_001.json`; exit code `0`; rows reconstructed `1024`;
  audit errors `0`; mismatches `0`.
- RTX 3080 Laptop GPU, CUDA 12.1; max CUDA allocation `1,177,100,800` bytes.
- The measured loop took `59.2858` seconds including per-bundle prefix
  prefill, but excluding model loading. This is descriptive and is not a
  speedup comparison.

`CONSTRUCTION_002.json` passed the final frozen mechanics checks and performed
zero categorical comparisons. `CONSTRUCTION_001.json` preserves the earlier
readiness attempt before the explicit model-file hash check was added.

The #4639 construction result still includes one selected-score tolerance
failure despite 9/9 unchanged winners. This new result answers only whether that
kind of score drift changes a winner across this complete corpus; it does not
revoke the predecessor's preregistered score gate.

## Provenance note

The standalone SHA-256 of `SOURCE_MANIFEST.json` was normalized by Git line
ending conversion on commit. `FORMAL_FREEZE.json` records the pre-stage worktree
hash (`cfe2…`), while the committed Git blob hashes to `3bfa…`. An additive
freeze audit confirms that all 12 files listed by that manifest match their
committed Git blob bytes exactly. The discrepancy is restricted to the
manifest's own digest field; source, runner, auditor, construction record and
formal inputs remain bound. See `FREEZE_AUDIT.md`; neither frozen metadata nor
raw outputs have been rewritten.
