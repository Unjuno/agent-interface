# Issue #6565 T0 — candidate-card parity

This narrow method-stage assay validates authored card parity and independent detection of planted confounds. It is not a human study and cannot establish whether preview order changes constraint recall, approval, burden, or preference.

The candidate crosses four fixed cases with three truthful presentations. The auditor separately reconstructs the expected source constraint, candidate effect, provenance, authority, facts, digest, preference status, and presentation order. Six isolated mutation controls cover recipient, format, provenance, unsupported endorsement, oracle leakage, and digest integrity. The preference-revision case is explicitly unscorable from the stated constraint.

Run locally:

```sh
python3 -B -m unittest discover -s research/analysis/preview_constraint_parity_6565_t0_20261002 -p 'test_*.py' -v
```

Formal allocation is one-shot and invoked only from the committed freeze receipt:

```sh
python3 -B research/analysis/preview_constraint_parity_6565_t0_20261002/runner.py
```

The runner checks the direct source/freeze commit chain, current `origin/main` ancestry, clean checkout, freeze sidecar, exact source hashes, OrbStack context, cached image identity, output paths, and container-name availability before starting the candidate. It then runs one candidate and one independent auditor in separate network-disabled containers. Runtime identities, exact argv, raw outputs, audit, inspect receipts, exit statuses, and hashes are retained under `results/formal_01/`. Any launch/audit failure is final for this allocation; no retries. Passing this assay is only card-construction/provenance readiness; human-impact claims still require separately governed T1.
