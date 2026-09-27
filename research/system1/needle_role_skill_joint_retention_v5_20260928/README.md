# v5 role-separated LoRA construction

Successor to #4941 after its one-shot Stage-0 exact-float-equality failure. This allocation preregisters an absolute 1e-6 tolerance for the duplicate-batch mean-loss numerical control and changes to fresh seeds. It stages one excluded-seed construction run behind a passing zero-update gate. See FREEZE.json and CONSTRUCTION_BOUNDARY.md.
