# T6 formal disposition — `STOP_AUDIT_MISMATCH`

- Allocation: `gluing-approx-irreversible-5537-t6-20261001-01`.
- Runtime: CPython 3.14.5/macOS arm64, host-local; no container, GUI, model, network, or external effect.
- Construction unittest: 5/5 pass; py_compile pass.
- Formal `python3 -B run_experiment.py`: one invocation, exit 0, 135 rows.
- Raw SHA-256: `0d11e234629f66bdacc7ed229125b0d5bff270f1976e10f1e766721beb13398b`.
- Independent `python3 -B audit_raw.py`: one invocation, exit 1, `STOP_AUDIT_MISMATCH`, zero base discrepancies, but only 5/6 frozen mutation controls rejected.
- Audit receipt SHA-256: `709d503eac07fecb6537b135f7d0667dd8d5bc7771aefb28aaa4d354b3dc36a7`.

## Read-only diagnosis

`false_admission` changes `rows[1].admitted` to `True`. That selected row is an exact, reversible action that was already admitted, so the transformation makes no change and the audit correctly cannot reject it. The raw/base audit itself reconstructs all 135 rows without discrepancy. This is a frozen mutation-control design defect; the preregistered 6/6 gate failed, so no scientific PASS is accepted and the formal/audit are not rerun or edited.

Retain this as STOP. A meaningful false-admission control and any further audit must use a new T7 allocation and path. This does not rewrite T5's independent 54-error STOP or T6's 5/6 mutation STOP.
