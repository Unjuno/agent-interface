# Intent-aligned local System-1 — pilot 01

This is a CPU-only synthetic mechanism pilot for open Issue #3442. It compares the same tiny network with and without an explicit versioned intent feature. The model proposes a bounded action class only; a deterministic check yields on stale intent/evidence or unknown intent identity.

- Frozen hypothesis, seeds and gates: [PREREG.md](PREREG.md)
- Exact construction failures and corrections: [CONSTRUCTION.md](CONSTRUCTION.md)
- Frozen runner: [runner.py](runner.py)
- Independent row/weight/split/metric audit: [audit.py](audit.py)

Run `python -B runner.py --construction-only` for construction checks. The formal runner emits its full JSON result to stdout and writes no local files. Feed that JSON on stdin to `audit.py`; the audit recomputes the held-out split, labels, model outputs from serialized weights, metrics, p95 and gate counts.

This allocation is host CPU/memory-only, not container evidence. It is synthetic mechanism evidence only—not a real Astra/GUI, online LoRA, role-network, skill-reuse or authority result.
