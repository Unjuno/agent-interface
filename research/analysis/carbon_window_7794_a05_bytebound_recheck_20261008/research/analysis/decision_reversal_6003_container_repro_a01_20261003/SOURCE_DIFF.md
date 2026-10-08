# Source lineage and exact deltas

The frozen fixture is byte-identical to #6003 host predecessor:

- Upstream branch: `research/issue6003-decision-reversal-t0-20261001`
- Upstream directory: `research/analysis/decision_reversal_6003_t0_v1/`
- `FREEZE.json`: unchanged; SHA-256 `8ff6c4d5d1594ab4623c52483b0f033a8aa6b5ede7f74ea71809461a9469352b`

Only presentation metadata changed in the scripts; decision tables, selector mathematics, constraints, and independent recomputation are unchanged:

- `select.py`: predecessor SHA-256 `f23ce27bed6d9c6de6e29b5715e667783d552ecbd73b049a80fc3e2955e3a316`; successor SHA-256 `9a608241404784526a951f6959fd737e6557abc28e41fe8f9a7b1e02a800ec53`. Sole delta: `scope` label changes from host-only to OrbStack container reproduction.
- `audit.py`: predecessor SHA-256 `e1bf0aca36389439bcbf693ed775ff038e297d7c0c6d4e5f27fab5916a46d4b2`; successor SHA-256 `85e125c0e082c13a50d3469ad575027004ad16d3fc53c33fd7e9ca7e18c94cae`. Sole deltas: output `status` and `scope` labels identify this container reproduction.

The predecessor's host-only raw result and independent audit are not copied into, edited by, or pooled with this allocation. Their retained hashes are recorded in `RUNBOOK.md` solely as parity targets.
