# T4 start gate and container plan

## Must re-check at 10:30 UTC, immediately before candidate

1. Re-read the newest #5085 and #5895 comments. Require the exact T4 allocation, this Codex thread ID, local macOS ARM64 OrbStack, and the 10:30–10:50 UTC exclusive window. T3 remains consumed and terminal.
2. Refresh main and PR #5630 head. Require the three frozen Git blobs and SHA-256s in `PREREG.md` unchanged. Record refreshed main SHA; if package base is stale, rebase without changing the frozen candidate/auditor/test contents and rerun tests.
3. Reconfirm `docker context show` is `orbstack`, daemon responsive, `docker info` architecture `aarch64`, exact image digest/platform locally present, and inspect all running/nonterminal containers. No unknown active container, ownership conflict, or unexplained overlapping allocation may remain. Do not stop/delete another owner's containers.
4. Check the absolute `results/formal-t4-01/output/` path is a real directory and empty, with host logs/CIDs in the sibling `receipts/` folder. Never mount the receipts folder to `/out`.
5. Recheck the window hasn't ended and start only once. If any gate is unavailable or changed, write a STOP receipt, invoke neither candidate nor auditor, do not retry, and release the slot by recording STOP on #5085.

## Candidate (exactly one container invocation)

Prepare the empty host output and separate receipt directories after passing the start gate. Capture docker stdout/stderr in the command result and copy them to `receipts/candidate.stdout.txt` / `.stderr.txt`; keep `--cidfile` at `receipts/candidate.cid`. Replace the three `<absolute path>` values only with the verified package, frozen target checkout, and empty candidate output paths.

```text
docker run --pull=never --platform linux/arm64 --user 501:20 --name unjuno-auditor-completion-5895-t4-candidate-8d0c7f53 --cidfile <absolute path>/results/formal-t4-01/receipts/candidate.cid --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m,mode=1777 --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --mount type=bind,src=<absolute path>,dst=/work,readonly --mount type=bind,src=<absolute path>,dst=/target,readonly --mount type=bind,src=<absolute path>,dst=/out,rw python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /work/run_candidate.py --target /target --out /out
```

After it exits, preserve `docker inspect` JSON under `receipts/candidate.inspect.json`. Only if candidate exit is exactly 0, and the `candidate_manifest.json` disposition and eight exits are exactly preregistered, invoke the independent auditor once.

## Independent auditor (only after candidate exit 0)

Mount package and frozen target read-only, candidate output read-only, and keep the new CID/logs outside those mounts. One exit only; no retry.

```text
docker run --pull=never --platform linux/arm64 --user 501:20 --name unjuno-auditor-completion-5895-t4-audit-8d0c7f53 --cidfile <absolute path>/results/formal-t4-01/receipts/audit.cid --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m,mode=1777 --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --mount type=bind,src=<absolute path>,dst=/work,readonly --mount type=bind,src=<absolute path>,dst=/target,readonly --mount type=bind,src=<absolute path>,dst=/results,readonly python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /work/independent_audit.py /results/candidate_manifest.json /target
```

Capture stdout/stderr, CID and `docker inspect` JSON separately. Preserve all evidence before removing only these exact owned exited containers. Never remove unrelated/stale containers.
