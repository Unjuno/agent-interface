# Issue #4423 retrospective publication

This publication does not rerun or retroactively preregister `o2-prefix-prune-q2n8-20260926-01`.

The original conversation-local handoff had 331 files and a 7,487,544-byte `tar.xz` with SHA-256 `71278cae3588b6e69b5e04b76e498c996c23a7950ffb61faaaeb4510058a6d18`. That full binary archive is not byte-published through this connector path. The public compact capsule retains all small source/plan/records/process receipts/audits plus the original MANIFEST and SHA-256/size commitments for every omitted `.rgb`/`.ait` file.

`verify_compact.py` is a postmeasurement read-only verifier. It does not invoke the consumed worker or timing allocation. It verifies every published original small file, all 192 omitted-file commitments, deterministically regenerates all 36 formal RGB inputs, independently rebuilds the 108 formal AIT packets using stdlib zlib, and recomputes timing/work/result gates from retained records and actual child exit receipts.

Local fresh restoration returns `PASS_LOCAL_EXACT_PREFIX_PRUNING`, 6,289 checks, errors `[]`, qualifier IDs `[4,10,16]`, regression IDs `[]`. The 48 omitted construction `.rgb`/`.ait` files are excluded-construction artifacts and remain hash-only commitments; this limitation is explicit.

Use:

```sh
python -B publication/restore.py /tmp/q2n8-public
cd /tmp/q2n8-public/research/measurement/o2_prefix_prune_q2n8_v1
python -B verify_compact.py
```

This is component CPU/codec evidence only. It is not runtime adoption, real-frame prevalence, end-to-end latency, model/token benefit, or product qualification.
