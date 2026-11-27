# R45 preparation

Attempt `win32-supervised-recovery-fresh-generation-task-20261024-r45-5f1e0c03c59e4455bcec72ca3dbf6797` is a new native-Windows one-shot based on the strict R44 sequence, with a separate phase-2 fixture source that timestamps completion of the exact `effect.json` write. The independent server oracle brackets its read of that same effect file. The sidecar preserves the effect JSON schema unchanged.

The frozen source and conditions are hashed in `conditions.json`. Only the two conditions needed to interpret the new endpoint differ from R44: a fresh task token/ID and write/read timing receipts. The strict release threshold, public standard caller, effect oracle, fresh-generation boundary, no-retry rule, timeout bounds, and cleanup gate remain inherited. Preflight is input-free; it must pass before the unique one-shot execution.
