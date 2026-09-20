# Reproduction

From the repository root, on a fresh allocation only, after freezing and verifying hashes:

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD:/src:ro" -v "$OUT:/out:rw" -w /src \
  --entrypoint python3 \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  -c 'import sys; sys.path.insert(0,"/src/research/issue_3784_focused_receiver_v1"); import runner; sys.argv=["runner.py","/src","/out"]; raise SystemExit(runner.main())'
```

The runner accepts only an empty output directory. Run it exactly once; never reuse or rerun a populated allocation. For the retained result, the exact formal invocation is in `results/host/formal-01.stdout.log` and `formal-01.stderr.log`; its source commit, runner, manifest, auditor, image and command are frozen in `PLAN.md` and this branch commit.

The independent auditor runs in a second no-network container. Mount source and formal evidence read-only and only a distinct empty audit directory writable:

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD:/src:ro" \
  -v "$PWD/research/issue_3784_focused_receiver_v1/results/formal-01:/evidence:ro" \
  -v "$AUDIT_OUT:/audit:rw" -w /src \
  --entrypoint python3 \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  -c 'import sys; sys.path.insert(0,"/src/research/issue_3784_focused_receiver_v1"); import audit; sys.argv=["audit.py","/evidence","/src","/audit"]; raise SystemExit(audit.main())'
```

The retained audit is under `results/audit-01/`; independent-container stdout/stderr are under `results/host/`.
