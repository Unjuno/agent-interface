# Reproduction

The image entrypoint is `python3` (not a shell). Run from the repository root after creating a new empty output directory:

```sh
docker run --rm --network none --read-only --tmpfs /tmp \
  -v "$PWD:/src:ro" -v "$OUT:/out:rw" -w /src \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  -c 'import sys; sys.path.insert(0,"/src/research/issue_3784_explicit_x11_receiver_v1"); import runner; sys.argv=["runner.py","/src","/out"]; raise SystemExit(runner.main())'
```

Do not reuse or clear an output directory. The runner rejects non-empty output and performs the four-row formal allocation once.

The auditor must run in a separate container with evidence and source mounted read-only and a distinct empty output directory. Import `audit.py` and pass `sys.argv=["audit.py","/evidence","/src","/audit"]` to `audit.main()` using the same pinned image and `--network none`. Preserve both output directories byte-for-byte.

