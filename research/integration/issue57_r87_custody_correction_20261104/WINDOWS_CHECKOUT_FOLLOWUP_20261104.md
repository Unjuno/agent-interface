# r87 Windows checkout and custody follow-up — 2026-11-04

This is an additive audit only. It did not replay the Calc task or change the preregistered outcome.

## Windows checkout effect

The audit was first run from a Windows worktree with system `core.autocrlf=true`. The `task-artifact.fods` Git blob and attempt manifest both have SHA-256 `20514fa067adcfc8a421f4586ed83ece7788c6a8e470c2638ee839da04e71f49` and 19,140 bytes. The converted worktree copy had SHA-256 `0da4e119caefff1d259de7dde0e65beec282e66bba4478f0999b567ed1e5e771` and 19,367 bytes. The first audit output (`audit_recheck_20261104_premerge.json`) therefore reported an additional artifact-hash failure caused by the checkout bytes, not by a new task result.

A `-text` rule now covers the r87 packet. Reconstructing worktree files from their Git blobs restored all 225 Git-verified entries. Two more entries (`docker-exit-code.json`, `docker-invocation.txt`) were reconstructed from their tracked LF blobs by LF-to-CRLF conversion; each reconstructed byte stream matched its frozen SHA-256 and byte count exactly. The r87 auditor then reported the parent artifact hash correctly and the original single frozen gate failure only. Its output is retained as `audit_recheck_20261104_restored_blob_bytes.json`.

## Remaining custody gap

Of 235 manifest entries, 227 now have exact hash-matching bytes available in the committed Git tree after those two hash-verified reconstructions. Seven log files remain absent from the r87 tree, and `experiment.py` remains one unrecovered mismatch: the tracked blob is 12,557 bytes, the frozen source is 12,562 bytes, and a plain LF-to-CRLF conversion does not match the frozen digest. No exact experiment-script copy was found in the scanned local repository. Four of the missing log hashes have byte-identical files in the separate r75 run on this PC; those were not relabeled or copied as r87 originals. The other three were not found in the scanned checkout.

The earlier custody audit is refined: two of its three tracked mismatches are exactly explained by line-ending normalization, while the experiment script is not recovered by that transformation. Raw custody remains incomplete; the original manifest and all absent/mismatched hashes are preserved. The scientific result remains `FAIL_OR_UNKNOWN` solely because the full-frame observation digest changed; this follow-up is not another live run, task success, provider accounting, efficiency, WSLc/MAP01, or reliability evidence.
The corrected, per-file availability and digest map is in [CUSTODY_CORRECTED_MANIFEST_20261104.json](CUSTODY_CORRECTED_MANIFEST_20261104.json). The original expected SHA list remains unchanged.

Reproduce the corrected byte inventory from the repository root with python research/integration/issue57_r87_custody_correction_20261104/verify_corrected_custody_manifest.py. The saved result is verify_corrected_custody_manifest_20261104.json.
