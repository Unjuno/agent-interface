# Issue #7712 T0 — exact discrete PID estimator qualification

Status: frozen before execution. This is a CPU-only finite synthetic construction test, not a GUI or agent observation experiment.

## H / T / D / C / U

**H.** A bivariate Williams–Beer `I_min` PID implementation over finite discrete variables will recover the precomputed redundancy, unique-information, and synergy atoms for exact redundancy, X1-only uniqueness, X2-only uniqueness, XOR synergy, null information, and an imbalanced target case. An independently implemented audit will reject changed source/target identities, missing probability mass, and a mutated joint distribution in the recorded result.

**T.** Freeze main `b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3`, the five integer-count joint distributions in `fixture.json`, candidate `candidate.py`, independent audit `audit.py`, tolerances, and mutations before running. Run the candidate once, then run the separate raw-only audit and three frozen corruption controls. Standard-library Python only; no network, model, game, GUI, OS input, container, GPU, or formal allocation.

**D.** `PASS_METHOD_SCOPED` iff the candidate returns all six expected PID tuples to absolute tolerance `1e-12`, atoms are nonnegative to that tolerance, the audit independently reconstructs every joint probability and PID atom from the frozen integer counts, the output binds the exact source/target names, and all three mutated records are rejected. Any candidate mismatch is `FAIL`; missing or malformed execution evidence is `HOLD`.

**C.** This qualifies only the selected `I_min` formula on exact, finite, tiny distributions. Different PID definitions can yield different atoms. The mutation controls prove rejection of these specific alterations only.

**U.** No finite-sample estimator, uncertainty interval, natural GUI channel, task/effect label, model, modality acquisition cost, paired ablation, action correctness, safety, or generalization is measured. No bits value grants action authority.

## Frozen method

For target `Y`, source-specific information is `I_spec(X_i;y)=sum_x p(x|y) log2(p(x|y)/p(x))`; redundancy is `sum_y p(y) min_i I_spec(X_i;y)`. Unique atoms are `I(X_i;Y)-R`; synergy is `I(X1,X2;Y)-R-U1-U2`. Logs are base 2; zero-probability terms contribute zero.

## Frozen input identities and execution

- Main ref: `b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3` (current at freeze).
- Candidate and independent auditor: local package files, SHA-256 recorded in `SHA256SUMS.txt` before execution.
- Fixture SHA-256 recorded in `SHA256SUMS.txt` before execution.
- Commands, Python version, raw outcome and audit outcome are retained in `RUN.txt`, `raw.json`, and `audit.json`.
