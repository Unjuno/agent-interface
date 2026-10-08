# Reverse-stress minimal-bundle T0 — #8594 A01

See [REPORT.md](REPORT.md) and [the owning Issue](https://github.com/Unjuno/agent-interface/issues/8594). This is a **scoped synthetic method PASS**, not product, model, live GUI, live DOOM, or operational-safety evidence.

The reviewable archive `bundle-a01.tar.gz` contains the independently auditable frozen `candidate.py`, `audit.py`, `spec.json`, `formal/raw_candidate.json` (first official raw), `formal/raw_audit.json`, exact process stdout/stderr/exit receipts and SHA-256 manifests.

```bash
sha256sum bundle-a01.tar.gz
tar -tzf bundle-a01.tar.gz
tar -xzf bundle-a01.tar.gz
python3 audit.py --spec spec.json --candidate-source candidate.py --input formal/raw_candidate.json --out verified_audit.json
```

Archive SHA-256: `ef43163ef12c2a596e38e051330aa14ac42244d802cc614343adbd58a76a4bea`. Compare the regenerated audit **semantic** result, not timing/hash fields, to the retained audit.
