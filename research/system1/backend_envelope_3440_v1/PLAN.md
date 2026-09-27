# System-1 backend envelope, allocation `system1-backend-envelope-3440-20260927-01`

Issue: https://github.com/Unjuno/agent-interface/issues/3440
Base: `609787159651da728b6a9158ed1ec052c77a897a`
Branch: `research/system1-backend-envelope-3440-20260927`
Evidence directory: `research/system1/backend_envelope_3440_v1/`

## H/T/D/C/U

- H: a shallow CART (depth at most 4) or fixed CPU MLP (11→16→16→6) trained on synthetic support can improve shifted-distribution correct-action coverage over an explicit conservative rule without sacrificing IID quality or authority boundaries.
- T: compare the frozen rule, deterministic greedy Gini CART, and fixed CPU MLP on identical deterministic trajectory rows. Training 512 rows; evaluate 1,024 IID, 1,024 shifted trajectory/noise, and the four explicit missing-target/stale, out-of-scope, low-confidence, and completed-goal controls. Training seed 8304391 is construction-only; formal seeds are 8304411, 8304421, 8304431. No retries, tuning, substitutions, or mid-run edits.
- D: `PASS_LEARNED_BACKEND_ADDS_SCOPED_COVERAGE` only if the same learned backend on all three seeds improves shifted exact in-scope coverage by ≥10 percentage points over rule; IID coverage is no worse than 2 points; actionable precision ≥0.99; every control produces exact REACQUIRE/YIELD/NO_ACTION as appropriate; p95 inference <60 ms; independent audit discrepancies = 0. Any miss is a negative result, not a retune.
- C: synthetic 2D target-control proposal selection only. No real-world actuation, task completion, provider call, GUI/OS input, or authorization is included. Safety checks are separate from the learned proposal and proposals have no side effects.
- U: result, run JSON, environment/command/source hashes, stop/failure reason, and independent audit are to be recorded append-only on Issue #3440; if promising, expose reusable code/report through this additive research path and a PR.

## Runtime and frozen schedule

Image `needle-pilot05:local`, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (`linux/amd64`, Python 3.12.14, PyTorch 2.5.1+cpu). Docker: network none, 1 CPU, 2 GiB memory, 64 pids, read-only root, read-only source mount, isolated writable result mount, no GPU. The image's default entrypoint must be overridden with `--entrypoint python`.

Commands:

```text
python -m unittest -v
python experiment.py --seed 8304391 --out /out/construction.json
python audit.py /out/construction.json
python experiment.py --seed 8304411 --out /out/formal-8304411.json
python audit.py /out/formal-8304411.json
python experiment.py --seed 8304421 --out /out/formal-8304421.json
python audit.py /out/formal-8304421.json
python experiment.py --seed 8304431 --out /out/formal-8304431.json
python audit.py /out/formal-8304431.json
```

No model output is executed. Construction is never counted as formal evidence. The independent auditor uses only the Python standard library and does not import the trainer or Torch.
