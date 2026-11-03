# r87-c11 custody correction (2026-11-04)

This addendum records a read-only audit of the r87-c11 packet present on the open PR #10185 branch. It does not change or rerun the consumed experiment, its frozen gate, or
its `FAIL_OR_UNKNOWN` outcome.

## Finding

The packet's `SHA256SUMS.json` lists 235 attempt files. Comparing it to the Git
tree at PR #10185 head `7a38f7fd2163d1cc8c973534ff1ef53784824ffb` found:

- 225 listed files match both byte count and SHA-256.
- Seven listed paths are absent from the Git tree: `apt-install.log`,
  `apt-update.log`, `container-runner.log`, `openbox.log`,
  `server-output/3d4a3e8db6524f9cb241d6e90bfef079/calc-launch-profile/user/GraphicsRenderTests.log`,
  `server-output/3d4a3e8db6524f9cb241d6e90bfef079/calc-launch.log`, and
  `xvfb.log`.
- Three tracked files differ from their manifest entries:
  `docker-exit-code.json` (tracked 107 bytes; manifest 112),
  `docker-invocation.txt` (tracked 677; manifest 678), and `experiment.py`
  (tracked 12,557; manifest 12,562). The tracked contents use LF line endings;
  this is not a CRLF normalization-only discrepancy.

The missing original log bytes have not been recovered. This addendum therefore
does not fabricate them or certify their contents. The three manifest entries
can be corrected from the currently tracked blobs, but original pre-commit
bytes remain unavailable unless recovered from an independent source.

## Interpretation and repair requirements

The custody claim that all attempt-file hashes were verified is not supported
by the committed tree. The separately verified screenshot receipts and pixel
audit are unaffected. The scientific gate is also unchanged: r87 remains
`FAIL_OR_UNKNOWN`; no same-frame pass, provider accounting, efficiency,
WSLc/MAP01, or broad reliability conclusion follows.

Before treating this packet as fully preserved, a follow-up must either recover
each missing original byte stream and verify it against the recorded hashes, or
retain an explicit unavailable-source record and a corrected manifest that
distinguishes verified Git blobs from unrecovered original files. Do not rerun
the consumed r87 attempt to fill the gap.

## Reproduction

From a checkout containing the packet:

```powershell
python research/integration/issue57_r87_custody_correction_20261104/audit_r87_custody.py
```

The script reads only Git objects and the committed manifest; it never modifies
the packet. Expected result on PR #10185 head `7a38f7fd` is 225 verified, 7 missing, and
3 mismatched entries.
