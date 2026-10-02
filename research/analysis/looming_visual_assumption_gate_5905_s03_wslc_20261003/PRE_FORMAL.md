# S03 pre-formal record

## Allocation and provenance

- Issue #6808; predecessor #5905; allocation `LOOMING-VISUAL-ASSUMPTION-GATE-5905-S03-20261003-01`.
- Owner task `01a0b990-3d17-72f1-a908-9a2072104ce5`.
- Frozen main `16cc4b523992bbd5131ee495d52a5bd16329e3d5`, observed 2026-10-02 20:59:08 UTC.
- Branch `research/5905-visual-assumption-gate-s03-wslc-20261003`; package path `research/analysis/looming_visual_assumption_gate_5905_s03_wslc_20261003/`; output path `execution/formal-s03/`.
- Source and fixture byte hashes are in `FREEZE.json` and `SHA256SUMS`. Builder, candidate, independent auditor, fixture/oracle, and 24 images copied byte-for-byte from S02's construction package; S02 was stopped before candidate and has no formal output. No claim of an independent source replication.

## Runtime and start checks

- WSLc 3.0.1.0, exact cached image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, amd64, Python 3.12.15. No image pull; network disabled; CPU only.
- At 2026-10-02 20:58:45 UTC, `wslc list --all` returned only the header and no containers; `wslc info` showed one default session. C: free 62,931,238,912 bytes. This snapshot is not reusable as the immediate stage gate; repeat complete inventory immediately before construction, candidate, and audit.
- Use bounded foreground `--rm` containers, read-only source, distinct output mounts. Do not touch foreign containers. Formal candidate/auditor count currently 0/0; retry 0.
- Window: 2026-10-02 21:00–21:15 UTC. Latest main, source hashes, image identity, output absence, WSLc inventory, process inventory, and storage must all be checked again before candidate. Any drift or unknown inventory is terminal STOP.

## Scope

Synthetic image-method fixture only. It establishes no live camera/game/controller/safety/benefit result. Frozen H/T/D/C/U and all raw gates are in README and FREEZE.
