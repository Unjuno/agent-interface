# Construction 01 — frozen Docker contract suite

Allocation: `temporal-resume-control-map-cleanup-20260928-01`
Source freeze: revision 02, commit `fdeca2c76e7f04385de94170f1a07a641f3c1df8`
Formal copied-evidence invocations at this point: runner 0/1, independent auditor 0/1.

No #4447 historical evidence, verifier, or source capsule was mounted. This was a synthetic-only test of cleanup receipt interpretation in the exact cached Python container image.

Command:

```sh
docker run --rm --pull=never --platform linux/amd64 --network none --read-only \
  --cpus=1 --memory=1g --pids-limit=64 --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16m \
  -v <frozen-study-path>:/study:ro \
  --entrypoint python \
  sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 \
  -B -S -m unittest discover -s /study -p test_contract.py -v
```

Observed host: OrbStack Docker Engine 29.4.0, linux/aarch64. Requested container platform: linux/amd64. Image identity was read from the local daemon and matches the exact ID used in #4534; no pull occurred. Network disabled; root filesystem and study mount read-only; 1 CPU, 1 GiB memory, 64 PIDs, bounded private `/tmp`.

Output:

```text
test_actual_temporary_directory_lifetime ... ok
test_cleanup_receipt_requires_present_inside_absent_after ... ok
test_missing_post_scope_observation_is_rejected ... ok
test_pre_context_observation_is_not_cleanup_evidence ... ok

Ran 4 tests in 0.003s
OK
```

Exit code 0. This validates only the cleanup receipt contract in synthetic inputs; it is not the copied-evidence result and does not pass the Issue hypothesis. No source changed after rev02 readback and before this run. No retry was needed.
