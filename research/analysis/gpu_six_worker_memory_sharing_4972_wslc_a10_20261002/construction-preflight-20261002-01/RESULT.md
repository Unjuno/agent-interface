# WSLc construction preflight 01

**Disposition:** `PASS_WSLc_CONSTRUCTION_PREFLIGHT_SCOPED`  
**Issue/allocation:** #6329 / `GPU-MEMORY-SHARING-4972-20261002-10`  
**Invocation:** 2026-10-02 01:13:23 UTC (filesystem receipt timestamps)  
**Source commit:** `7999f5628623d024f713f4ecc3577ad04ee09ae7`

## H / T / D / C / U

**H.** The frozen audit-contract suite and non-root writable output bind work in the cached PyTorch image through Microsoft WSL Containers, with networking and GPU access disabled.

**T.** One construction-only WSLc container was invoked with `--rm --pull never --network none --cpus 1 --memory 1G --user 65534:65534`; the package source was mounted read-only at `/src`, and only this fresh evidence directory was writable at `/construction`. Command: `wslc.exe run --rm --pull never --network none --cpus 1 --memory 1G --user 65534:65534 --mount type=bind,source=<package>,target=/src,readonly --mount type=bind,source=<evidence>,target=/construction --env PYTHONDONTWRITEBYTECODE=1 pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 python /src/construction_check.py /construction/write_probe.txt`. No `--gpus` option was supplied. Candidate, CUDA worker, and formal auditor were not invoked; no retry.

**D.** Container exit was 0; all 10 tests passed; the non-root bind probe bytes match exactly; post-run WSLc container inventory is empty; inspected image config ID is `sha256:048a0de5d4322054f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32`, platform linux/amd64, and the pinned registry digest is present. The independent host-side receipt auditor's first version returned `FAIL_PREFLIGHT_RECEIPT` because it incorrectly expected repository+digest in one token from WSLc's table output. That first receipt is preserved as `PREPARATION_AUDIT.json`. After correcting the auditor's parsing (not changing experiment outputs), the recheck returned `PASS_WSLc_CONSTRUCTION_PREFLIGHT_SCOPED` in `PREPARATION_AUDIT_RECHECK.json` with zero errors.

**C.** This validates only the local runtime/mount/test construction for the exact source snapshot. Main advanced during this work; no immediate-at-invocation main SHA was captured, and the formal runner will require a fresh refreeze and exact assigned interval before candidate launch. WSL emitted: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” No hard memory+swap or PID isolation is claimed.

**U.** This is not a six-process CUDA result, model/agent workload result, resource-isolation proof, or product/speed claim. It does not authorize a candidate. GPU allocation remains deferred/unassigned under #5085.

## Evidence files

- `stdout.txt`, `stderr.txt`, `exit_code.txt`: raw container output and status.
- `write_probe.txt`: exact output from UID 65534 through the writable bind.
- `containers_after.txt`: post-run empty container inventory.
- `image_inspect.json`, `images_digests.txt`: cached image identity evidence.
- `audit_preflight.py`: independent host-side receipt auditor.
- `PREPARATION_AUDIT.json`: preserved first auditor defect/false negative.
- `PREPARATION_AUDIT_RECHECK.json`: corrected independent receipt audit.
