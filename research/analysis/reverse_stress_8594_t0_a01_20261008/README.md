# Reverse-stress minimal-bundle T0 — #8594 A01

See [REPORT.md](REPORT.md) and [the owning Issue](https://github.com/Unjuno/agent-interface/issues/8594). This is a **scoped synthetic method PASS**, not product, model, live GUI, live DOOM, or operational-safety evidence.

The reviewable archive `bundle-a01.tar.xz` contains the independently auditable frozen `candidate.py`, `audit.py`, `spec.json`, `formal/raw_candidate.json` (first official raw), `formal/raw_audit.json`, exact process stdout/stderr/exit receipts and SHA-256 manifests.

```bash
sha256sum bundle-a01.tar.xz
tar -tJf bundle-a01.tar.xz
tar -xJf bundle-a01.tar.xz
python3 audit.py --spec spec.json --candidate-source candidate.py --input formal/raw_candidate.json --out verified_audit.json
```

Archive SHA-256: `c31cb1d9145f80e9f225a8e7bade382ecf46a2d1c6e47a2f6e3dfaf1fafa9172`. Compare the regenerated audit **semantic** result, not timing/hash fields, to the retained audit.
