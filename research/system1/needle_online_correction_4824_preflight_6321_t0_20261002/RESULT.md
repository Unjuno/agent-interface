# Issue #6321 CPU dataset preflight and audit successor

This package contains the CPU-only label/split preparation for the proposed online Needle LoRA adaptation in #6321. It deliberately does not include or claim the GPU training allocation.

The experiment ran locally at the path recorded in its frozen `FREEZE.json`. Before publication, a same-named remote branch appeared at the original main base with no associated PR. To avoid writing to that possibly parallel-owned branch or its reserved path, this evidence package is published under a distinct additive path and branch. `PUBLICATION_NOTE.md` preserves the mapping; frozen run identities and raw bytes are unchanged.

## Result and retained STOP

The original OrbStack preflight allocation `NEEDLE-ONLINE-CORRECTION-4824-CONSTRUCTION-20261002-01` generated the frozen dataset and a first audit output, but the top-level runner failed after child processes with `KeyError: 'image_id'`. Its authoritative disposition remains `STOP_RUN_RECEIPT_POSTPROCESS_KEYERROR`, not PASS. See [STOP_REPORT.md](STOP_REPORT.md) and original `results/preflight-01/` files. The data itself was not regenerated.

A separately frozen, independent, audit-only successor read the exact immutable raw dataset once in OrbStack. It returned exit 0 and `PASS_DATA_AUDIT_SUCCESSOR_SCOPED`: all three seeds, 984 rows, split/role/ID/feature/label conditions, and 7/7 corruption controls reconciled with zero errors. See [audit_successor/PLAN.md](audit_successor/PLAN.md), [FREEZE.json](audit_successor/FREEZE.json), [RUN.json](audit_successor/results/audit-01/RUN.json), and raw audit output. Candidate invocations 0; auditor 1; retries 0. This successor does not overwrite or promote the original runner STOP.

The confirmed target functions are A: class 0 for every feature vector; B: class 1 iff feature 0 is 1. Support/arrival/held-out examples are disjoint by feature vector within each role and seed. The exact data hash is `dad06f71a4a7acfd4ce110852ce5ee82f5e2ce654e1cf0f1d4401106f2edd188`.

## H / T / D / C / U

- **H:** A separate raw-only checker catches the predecessor's role-label inversion before fitting.
- **T:** Three specified seeds; A-support 64, B-arrival 8, A-held-out 128, B-held-out 128 each. Candidate generation was one-shot; after its wrapper STOP, a fresh audit-only allocation checked the unchanged data once in an offline, read-only-source/root, CPU-bounded OrbStack container.
- **D:** Independent audit PASS only if 984 rows and all seed/split/target/lineage/disjointness/balance gates reconcile, with 7/7 mutations rejected. This criterion passed in the audit successor; original allocation still has the separate runner STOP.
- **C:** Deterministic label and split integrity only; no model/optimizer or CUDA.
- **U:** Does not test A-retention, B-acquisition, routing, competence, online update quality, GPU placement, live GUI, or product benefit. The exclusive RTX 3080 WSLc lease is still ungranted.

## Environment and safeguards

The cached `python:3.12-alpine` image ID `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b` ran on OrbStack `linux/arm64`. Network was disabled; root/source were read-only; CPU 0.25, memory 128 MiB, PIDs 32. No pre-existing container was modified. No CUDA/GPU/optimizer/GUI/WSLc calls occurred.

Construction tests: 6/6 for generation, plus 3/3 for the independent audit successor. A pre-freeze audit-construction test caught a transcribed SHA-256 with one extra trailing `0`; the checksum was corrected before the successor freeze and formal audit. No experiment input was changed.
