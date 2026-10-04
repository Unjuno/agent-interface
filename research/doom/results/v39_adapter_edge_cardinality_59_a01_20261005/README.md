# V39 adapter-edge duplicate cardinality

## H / T / D / C / U

- **H:** For one V39 identity, a duplicated adapter DOWN or UP row must make the receipt incomplete and expose neither timing interval. Exact-one cardinality is needed because duplicate telemetry can be identical and evade field-consistency checks.
- **T:** A01 replays one retained V39 fixture through the frozen controller projector with a unique baseline and five duplicate treatments: identical DOWN, identical UP, both identical, conflicting DOWN, and conflicting UP. A weakened first-row-wins guard is the negative control. A02B reruns the added regression against current #7602 source and the exact test file proposed by this PR.
- **D:** A01 passes when the unique baseline pairs, all five duplicate cases fail closed with null endpoints, first-row-wins pairs the duplicates, and an independent raw-derived audit detects a coherent false pair. A02B passes when the exact pinned test method passes all five subcases and exact test/controller files byte-compile.
- **C:** A01's five duplicates failed closed; first-row-wins falsely paired them. Audit-v2 passed 66 checks and its tamper control detected a coherent duplicate-pair corruption. A02B passed one test method with five duplicate subcases against the current #7602 head. See `AUDIT_A02B_RESULT.json` and `raw/a02b-container.log`.
- **U:** This is deterministic projection evidence from one retained synthetic trace. It does not establish physical X-server key release, application consumption, useful task feedback, live threat response, recovery benefit, or MAP01 completion.

## Frozen source and fixture

A01 used controller head `64c48e95425972bc04e61a41d219686c789cb6b6`, Git blob `2c42c71985e3a8e16bba11cba3f99181798893d8`, SHA-256 `888c3a8f5ea682e0e63d4f63c71a737877829c5a893b427de118d1be958fba8a`. The fixture Git blob is `eacb735634d6c6761ba7fa39448e6d7d43e342d5`, SHA-256 `ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e`. A01 source, candidate, raw output, auditor, and audit-v2 are retained separately here.

A02B starts from current #7602 head `a7f9e9e3c4bd31199bde3a14761783ead619ad08`. Controller snapshot: blob `7494e8f217dc86e94cb1bca2fd37475cd53b7e9c`, SHA-256 `41329ce5735aa80b0cb6710c10f2c2bf9627f3b22e57faf197cf37eef335129a`. Proposed test snapshot: blob `0d90a558b96f0734f5ddc4ca3e91703642646f37`, SHA-256 `b82a97f32d51749988df059c963ccc163dfbfe5f294ff33aebcc39854173fb5b`. Exact snapshots, runner, and pre-run freeze are under `a02b-current-source/`, `candidate/run_a02b_current.py`, and `AUDIT_A02B_FREEZE.json`.

## Execution and audit provenance

A01 candidate, preliminary auditor, and audit-v2 each ran in one pinned WSLc container and exited 0. Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; `--network none`, one CPU, 512 MiB memory, read-only source/evidence, separate output, `--pull never`, and `--rm`. WSLc reported unavailable swap limits; `memory.swap.max=max`, so no swap-constrained claim is made.

The earlier A02 attempt is preserved in `historical-a02-reconstructed/` but is not accepted as raw audit evidence. Its temporary accepted-run output was removed before preservation. The exact corrected runner SHA `7b8357034cb3c5aa80e39720478238b3c142b55c56eb2df51924bd423c9f7f9c` was not found in available output workspaces. The recorded test blob and SHA were recovered and preserved; the failed first runner is labeled as such. Reconstructed result/transcript files are not represented as raw output.

A02B ran the current proposed test against current #7602 source once in the same pinned, network-isolated WSLc image and limits. It passed one test method with five duplicate subcases and byte-compiled both exact files. Result and console transcript are retained under `raw/`. The pre-run `wslc list` command was invoked, but its output file was not captured; this package makes no claim that the preflight inventory was empty. A post-run list capture returned exit 0 with blank stdout and is preserved verbatim.

## Package verification

`verify_package.py` checks A01 source/fixture/script identities and the raw-derived audit-v2 result; A02B source, test, runner, result, and execution metadata; safe unique manifest paths; every SHA-256 entry; and equality between the manifest and all tracked package files except `SHA256SUMS` itself. It excludes every `__pycache__/` directory and `*.pyc` deterministically. The verifier itself is included in the manifest. The README is UTF-8 LF and is byte-preserved under the repository `research/doom/** -text` rule.
