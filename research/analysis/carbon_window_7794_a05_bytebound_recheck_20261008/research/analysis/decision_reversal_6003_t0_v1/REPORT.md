# Result — Issue #6003 T0-host-01

**Outcome: `PASS_HOST_ONLY_CONSTRUCTION`; the Issue's disposable-container condition remains untested.**

## Executed experiment

- Base main: `5759a6e65b8b5e7487fb2ad61f53bb531aeaf512`; allocation `6003-t0-host-20261001-01`.
- Runtime: Windows 10 host, Python 3.11.9, standard library only.
- Candidate command, executed once: `python .\select.py` (exit 0, 2026-10-01 12:28:33 UTC).
- Separate independent audit, executed once: `python .\audit.py` (exit 0, 2026-10-01 12:28:38 UTC; `errors=[]`). The auditor imports no selector code.
- No GPU, model, Docker, WSL, package installation, external inference, or empirical observations were used.

## Observed finite-table result

| Rule | Selected result | Frozen criterion |
|---|---|---|
| Cheapest-first | `A-cheap-irrelevant` | cost 1; feasible with mandatory sentinel |
| Nominal entropy | `A-cheap-irrelevant` | 2.0 bits under nominal fixture |
| Worst-case decision reversal | `B-robust-reversal` | minimum reversal mass 0.60 across four illustrative scenarios |
| Null control | `UNRANKABLE` | all robust scores are 0; no downstream action changes |

The prior-sensitivity control also reversed the entropy ordering of B and C: nominal entropy C=1.5848 > B=1.2955 bits; capture-lean entropy B=1.2955 > C=0.9219 bits. A's four equiprobable outcomes carry 2 bits but never change the downstream action in the authored table. Infrastructure `STOP` probability is excluded from reversal mass and is not scientific support.

## Interpretation and limitations

This validates only that the frozen finite-table implementation and independent arithmetic agree on the authored controls. Priors, outcomes, states, costs and action consequences were constructed for this test; the result is not calibrated expected utility, real experiment value, evidence of improved research productivity, a GPU/model result, or a roadmap decision. Because Docker inventory was unavailable, this host-only run does **not** pass the exact disposable-container condition in #6003's proposed T0. Preserve the result with that qualification; do not silently upgrade it to a container or field PASS.

## Artifact digests (SHA-256)

- Freeze: `8ff6c4d5d1594ab4623c52483b0f033a8aa6b5ede7f74ea71809461a9469352b`
- Candidate source: `f23ce27bed6d9c6de6e29b5715e667783d552ecbd73b049a80fc3e2955e3a316`
- Independent auditor: `e1bf0aca36389439bcf693ed775ff038e297d7c0c6d4e5f27fab5916a46d4b2`
- Candidate raw output: `0a267821274056f87a3c6beace29b50623865382c2fe4dda0d0bba9e150af57b`
- Independent audit output: `9a5e32bf1a1e76437d9989e886c263223b35625f77ee0d5ee6e59a9c1f3b78c9`
- Method record: `c1d8e911647f6d31cec57409d2d511e803420921b41dcf97b83ece1fe4e5293d`
