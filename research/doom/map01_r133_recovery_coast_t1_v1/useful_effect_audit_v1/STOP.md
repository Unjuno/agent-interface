# Immutable v1 first outcome

**Disposition: `STOP_INTEGRITY / counterbalance_order`.** Candidate `python3 -B candidate.py` ran once and exited 0; the independent auditor `python3 -B audit.py` ran once and exited 0 but correctly found five audit errors because every adjudication stopped at `counterbalance_order`. Retries: 0. The v1 candidate enumerated recovery/coast within each pair, which conflicts with the frozen expected order `(1 recovery, 1 coast, 2 coast, 2 recovery, 3 recovery, 3 coast)`. No scientific counterexample was evaluated in v1. Preserve its raw and audit unchanged; v2 is the distinct corrected successor.

- Freeze source base: `5759a6e65b8b5e7487fb2ad61f53bb531aeaf512`
- Candidate raw SHA-256: `e30e642fbf9ada2091a76a292de81dee505492c3ead88d77f32b093dec81e797`
- Audit SHA-256: `fda797b4b086e490b422faa235451d6e225856a1b6fa170a2d480268cc3cb4ee`
- Candidate stdout SHA-256: `4ea8e98bd367c0cb468337726beb50d89af907c8069814fe883bb46ea4713b80`
- Audit stdout SHA-256: `18995b578240dbf3a4d2bc3a9f023ff6b0ed04946395ef2c42f87455be7abf39`
- Container, GUI, game, model, input, GPU: not used.
