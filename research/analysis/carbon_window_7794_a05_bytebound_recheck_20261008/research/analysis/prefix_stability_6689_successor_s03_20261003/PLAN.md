# Frozen experiment plan — successor #6689 S03

Question: Does preserving explicit pending mandatory-vector obligations prevent an early terminal disposition after a mandatory failure followed by generation sealing, while allowing complete negative decisions to finalize even when optional sources remain open?

Frozen allocation: PREFIX-STABILITY-6689-S03-WSLC-20261003-01. Candidate and auditor execute once each in separate CPU-only WSLc containers; a third one-shot container runs auditor mutation controls. No GPU, GUI, external network, model, user data, retries, or production effects.

Pass criteria: all five candidate rows match independent reconstruction; incomplete mandatory vector stays pending; completed negative may finalize without optional-source closure; positive requires generation sealing; metric fields remain separate from classification counts; all five mutations are rejected. Failure modes are FAIL_METHOD, FAIL_AUDIT, or STOP as applicable.

Limits: deterministic synthetic fixture, stdlib-only; no production integration or external ground truth.
