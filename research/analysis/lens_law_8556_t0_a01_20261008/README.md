# Lens-law conformance finite simulator (Issue #8556)

This additive package tests whether scoped Get–Put, Put–Get, and Put–Put checks expose seeded observation/update adapter defects beyond final-label-only and same-input replay baselines.

It is a deterministic authored finite model, not a live GUI or application experiment. Declared semantic fields, totality, idempotence, side-effect assumptions, epochs, and completion states define the scope. The independent audit implementation does not import the candidate implementation.

See PROTOCOL.md for H/T/D/C/U, runtime boundary, and stop criteria. RUN_RECORD.md reports execution evidence; CONSTRUCTION_LOG.md distinguishes test-driven construction from the formal run. Formal outputs are under results/.

Reproduce in this directory with Python 3.12:

    python -B -m unittest -v test_candidate.py test_audit.py
    python -B candidate.py --input input.json --output results/candidate.json
    python -B audit.py --input input.json --candidate results/candidate.json --truth truth.json --output results/audit.json

CLI output paths use exclusive-create: do not overwrite existing evidence. Formal commands execute once only, per the protocol.
