# Reproduction

Use the pinned image directly; its entrypoint is Python 3. Keep source/root read-only and each output mount distinct and initially empty. Never rerun a formal allocation into an existing path.

Construction test (from repository root):

```sh
docker run --rm --network none --read-only --tmpfs /tmp \
  -v "$PWD:/repo:ro" -w /repo \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  -c 'import sys,unittest; sys.path.insert(0,"research/issue_3784_explicit_x11_receiver_v3"); s=unittest.defaultTestLoader.discover("research/issue_3784_explicit_x11_receiver_v3",pattern="construction_test.py"); raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(s).wasSuccessful())'
```

Formal run and independent audit commands are frozen with their source, manifest and auditor hashes in PLAN.md before allocation. Both use `--network none`; auditor receives evidence and source read-only and writes only to a separate empty audit directory.

