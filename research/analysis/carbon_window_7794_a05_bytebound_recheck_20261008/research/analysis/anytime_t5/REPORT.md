# Anytime validity T5 — branch dependence and filtration audit

Issue: [#5446](https://github.com/Unjuno/agent-interface/issues/5446)
Task: `ISSUE-5446-ANYTIME-T5-20260930`
Disposition: `PASS_WITH_AUDIT_AND_EXECUTION_PROTOCOL_DEVIATIONS`

## Decision and scope

In this exact synthetic null, three likelihood-ratio processes that respect a fixed or predictable filtration stayed at a 25% false-commit probability across all four tested cross-branch dependence levels. Post-hoc selection of the best branch exceeded the nominal Ville bound of 50% at rho=0 (57.8125%) and rho=1/4 (50.4883%). A predeclared equal-weight mixture stayed within the bound at every rho. The result supports recording branch-selection/aggregation rules as part of an evidence-process contract; it does not show that arbitrary correlated verifier outputs are valid e-processes.

The candidate was inadvertently invoked twice: the first invocation wrote `raw/formal.json`; after its output was not visible through the tool wrapper, a second identical command was issued to display it. Both invocations used the identical frozen deterministic source, model, and parameters; there is no RNG, and the second displayed JSON matched the retained first output. The second stdout was not saved as a separate raw artifact. This violates the preregistered one-invocation protocol and is retained as an execution deviation, although it does not add sampling or alter the exhaustive state space. The first independent-auditor invocation returned FAIL solely because the auditor compared the string `1` against `1/1`; exact `Fraction` arithmetic and every policy fraction/decimal had been reproduced. The original FAIL is retained unchanged in `raw/audit.json`. An additive audit correction changed only the total-mass string check to parse exact rational values; the corrected independent audit passes and is retained as `raw/audit_v2.json`. No source, parameter, or result tuning occurred. The exact synthetic result is supported, but both deviations are disclosed rather than silently recast as a clean preregistered PASS.

## H/T/D/C/U

- **H:** Under time-independent shared/private Bernoulli(1/2) branch vectors, fixed-A, fixed equal-mixture, and a history-only predictable selector remain within the 1/threshold bound. Post-hoc best-of-branch selection can exceed it.
- **T:** Exact rational enumeration over horizon 4, three branches, threshold 2, and rho in `{0, 1/4, 1/2, 1}`. At each time, all branches share one fair bit with probability rho; otherwise their bits are independent fair draws. Candidate and auditor use separate implementations.
- **D:** The independent corrected audit reproduces all exact results, total mass is one, valid processes are at or below 0.5, and post-hoc selection exceeds 0.5 at rho 0 and 1/4. Four corrupted copies are rejected. Caveats: audit v1's serialization assertion failed and was corrected after the allocation; the deterministic candidate command was inadvertently invoked twice despite the preregistered one-invocation rule. The first raw formal output is unchanged.
- **C:** If inflation is absent under a different dependence structure, that would bound this particular selection/model combination only; it would not make unrestricted post-hoc branch choice valid.
- **U:** The model assumes time-independent branch vectors, Bernoulli(1/2) marginals, and correctly specified likelihood ratios. Shared/private exchangeable dependence is not adversarial or temporal dependence. No real verifier, semantic correctness, action outcome, calibration, or product-level claim is tested.

## Frozen execution

Preregistration was posted to Issue #5446 before execution (comment ID `5910422478`). Frozen candidate SHA-256: `06677dc7f48fba6ab0d5860c4b601b3d92d5913994d16cc84ee586154f2a7b67`.

- Command: `docker run --rm --network none -v "$PWD/research/analysis/anytime_t5:/work:ro" python:3.12-slim python /work/experiment.py`
- Engine: OrbStack Docker Engine `29.4.0`, `linux/arm64`
- Image: `python:3.12-slim`, local image ID/digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Randomness: none; exact rational exhaustive enumeration. Positive-mass paths: 4096 for rho 0, 1/4, 1/2; 16 for rho 1.
- Horizon: 4; branches: 3; likelihood-ratio factors: 3/2 on 1, 1/2 on 0; threshold: 2.

The predictable selector chooses a branch before seeing each time's vector, using only its previously selected bit: advance branch index by +1 mod 3 after 1 and +2 mod 3 after 0. The fixed mixture is the arithmetic mean of the three wealth processes at each time. Post-hoc max commits if any complete branch's running process crosses threshold.

## Results

Exact null false-commit probabilities (decimals in parentheses):

| rho | fixed A, anytime | post-hoc max branches | fixed mixture | predictable selector | fixed A, final only |
|---:|---:|---:|---:|---:|---:|
| 0 | 1/4 (0.25) | 37/64 (0.578125) | 529/4096 (0.129150) | 1/4 (0.25) | 1/16 (0.0625) |
| 1/4 | 1/4 (0.25) | 517/1024 (0.504883) | 179425/1048576 (0.171113) | 1/4 (0.25) | 1/16 (0.0625) |
| 1/2 | 1/4 (0.25) | 109/256 (0.425781) | 13297/65536 (0.202896) | 1/4 (0.25) | 1/16 (0.0625) |
| 1 | 1/4 (0.25) | 1/4 (0.25) | 1/4 (0.25) | 1/4 (0.25) | 1/16 (0.0625) |

The fixed and predictable policies equal 0.25 for every rho: each selected next observation has a fair marginal conditional on the previous-time history because time vectors are independent. The equal mixture is a convex mixture of branch martingales, including under cross-branch dependence. The post-hoc maximum is not that mixture and crosses 0.5 under low dependence. At rho=1 the branches are identical, so the post-hoc inflation disappears.

## Audit and retained raw evidence

The independent auditor re-enumerated the shared/private vector probabilities and all 4-time paths without importing candidate functions. Corrected audit: `PASS`, 0 errors, 4 rho rows. Corruption controls rejected 4/4 mutations: threshold, missing rho row, exact probability, and decimal probability.

| artifact | SHA-256 |
|---|---|
| `experiment.py` (frozen candidate) | `06677dc7f48fba6ab0d5860c4b601b3d92d5913994d16cc84ee586154f2a7b67` |
| `audit.py` (corrected post-allocation audit) | `943fdb729381681cdd4546335a06b294f86362ddf7f4483efee75641e63925e9` |
| `corruption_controls.py` | `1de9e690dc3cb1e420cf094a89c816b22cce40f27e4940f07f0af97b734a44ea` |
| `raw/formal.json` | `edd6a91f389bb558b391a2751e86b58417e1953eedf284858d2047d0ba1061ee` |
| `raw/audit.json` (original FAIL; preserved) | `8167ae7ecf0c9174adec1bd47b63ed54022650d7c2f779659d86d67988f1150b` |
| `raw/audit_v2.json` | `0aae03730fa5e7e4751c39bfcca3d9df5b285d3bf86cd03946ed3f312760f87a` |
| `raw/corruption_controls.json` | `cb2e07dd0d030c254b08f4963afbdbffa29e900ae52675d0837ac447698b1805` |

## Stop and follow-up boundary

The exact allocation is closed; no further candidate executions or parameter tuning. A distinct future test would need temporal dependence or misspecified marginals, and must test a process valid for the declared conditional null rather than carry the present iid-over-time guarantee forward. The immediate interface consequence is narrow: encode verifier-selection timing, aggregation rule, dependency contract, and `NOT_VALIDATED` state when those are absent.
