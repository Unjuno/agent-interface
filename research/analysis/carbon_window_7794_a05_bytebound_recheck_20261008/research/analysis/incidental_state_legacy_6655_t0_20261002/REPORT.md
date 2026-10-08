# Issue #6655 / #6686 WSLc successor T0 result

## Outcome

`PASS_METHOD_SCOPED` for the finite synthetic method fixture. This validates scorer/auditor behavior under the recorded WSLc environment only; it does not establish a real-interface effect, human benefit, or downstream causal transfer.

The first Windows-host allocation remains a separate protocol deviation recorded on #6655. It was not edited, reused, or pooled.

## Runtime and protocol

- WSL 3.0.1.0, `archlinux`, native WSLc.
- Image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; local image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`; Python 3.12.15.
- Pull disabled, network none, CPU 1. WSL warned cgroup/swap memory enforcement is unavailable; a 512m request was made but effective memory limiting is not claimed.
- No GPU, model, GUI, user data, or external effects.
- Construction 9/9 passed inside WSLc. Candidate 1/1, exit 0. Separate raw-only auditor 1/1, exit 0. Retries 0.

## Findings

The 224-row synthetic fixture distinguished the designed classes. Helpful inherited view: mean observations 1.0 vs 3.0 (inherit vs reset); harmful stale filter: correctness 0.0 vs 1.0, while mean total cost was 3.0 vs 4.0; irrelevant theme did not change correctness or observations; required saved effect remained correct under both arms. Three non-comparable cases were excluded from scored outcomes.

These are descriptive outputs in a hand-authored finite simulator, not an empirical treatment effect.

## Immutable artifacts

- Candidate raw: 226,381 bytes, SHA-256 `7ef2eb20a4159eadcda498b05ad0755632136d671abb2db83fab9ae3f801156c`.
- Auditor JSON: 1,533 bytes, SHA-256 `d6053d1f18a0aea4ba2b78133a86b3fb02ff36871eeca0c203c2f53628fd416e`.
- Raw bytes are stored in the Git blob at `f935c5faddcc94c10166d6079c08b99f6f3df265`; auditor bytes at `3a8c48a557405c7fa73620913fdf64c704018fa9`. RUN_RECORD maps these IDs to their paths.

No conclusion beyond `PASS_METHOD_SCOPED` is authorized.
