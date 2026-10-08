# Issue #8597 T0 A01 — tail-regret ranking sensitivity

Deterministic synthetic finite evaluation of whether upper-tail opportunity regret can reverse route ranking when means tie. See `PROTOCOL.md` for H/T/D/C/U and scope. #8528's result is a fixed semantic reference; no #8528 files are modified.

Formal commands, each once after freeze:

```sh
python -B candidate.py --dir .
python -B audit.py --dir .
```

Construction checks are separate and do not increment formal invocation counts.
