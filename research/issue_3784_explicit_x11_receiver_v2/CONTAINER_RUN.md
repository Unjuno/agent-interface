# Reproduction

The pinned image entrypoint is Python 3. Use distinct empty output directories for formal evidence and independent audit. Never rerun into an existing directory.

Formal command from the repository root:

```sh
docker run --rm --network none --read-only --tmpfs /tmp \
  -v "$PWD:/src:ro" -v "$OUT:/out:rw" -w /src \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  -c 'import sys; sys.path.insert(0,"/src/research/issue_3784_explicit_x11_receiver_v2"); import runner; sys.argv=["runner.py","/src","/out"]; raise SystemExit(runner.main())'
```

Run the independent `audit.py` in another container with source and evidence read-only, a separate empty audit output mount, and `sys.argv=["audit.py","/evidence","/src","/audit"]`.

