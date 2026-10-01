# Construction-only auditor check

Before freezing, the independent auditor's finite enumeration and corruption
controls were exercised on masks 1, 11, and 19 only; no #4449 formal raw was
read during this check. The pinned OrbStack Python image ran:

```sh
docker --context orbstack run --rm --pull=never --platform linux/arm64 \
  --network none --read-only --cpus=1 --memory=256m --memory-swap=256m \
  --pids-limit=32 --cap-drop=ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --workdir /study \
  --mount type=bind,source="$AUDIT_STUDY",target=/study,readonly \
  --entrypoint python \
  sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e \
  /study/audit.py --self-test
```

Retained stdout:

```json
{"controls": [{"control": 1, "effective": true, "rejected": true}, {"control": 2, "effective": true, "rejected": true}, {"control": 3, "effective": true, "rejected": true}, {"control": 4, "effective": true, "rejected": true}, {"control": 5, "effective": true, "rejected": true}, {"control": 6, "effective": true, "rejected": true}, {"control": 7, "effective": true, "rejected": true}, {"control": 8, "effective": true, "rejected": true}, {"control": 9, "effective": true, "rejected": true}, {"control": 10, "effective": true, "rejected": true}], "decision": "PASS_SELF_TEST", "errors": [], "rows": 10}
```

This is only the excluded self-test of the auditor and its mutation targets;
it does not inspect or rerun the consumed formal allocation.
