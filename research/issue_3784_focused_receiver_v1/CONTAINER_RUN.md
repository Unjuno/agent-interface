# Reproduction

From repository root, after freezing and verifying hashes:

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD:/src:ro" -v "$OUT:/out:rw" -w /src \
  --entrypoint python3 \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  -c 'import sys; sys.path.insert(0,"/src/research/issue_3784_focused_receiver_v1"); import runner; sys.argv=["runner.py","/src","/out"]; raise SystemExit(runner.main())'
```

The runner accepts only an empty output directory. Run it exactly once. The independent audit is a new no-network container with source and formal evidence read-only, and only its distinct empty `/audit` mount writable; set `sys.argv=["audit.py","/evidence","/src","/audit"]` and invoke `audit.main()`.
