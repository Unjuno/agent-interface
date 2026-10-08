# GPU-candidate triage archive status

`local_gpu_candidate_triage_20260928.md` is preserved byte-for-byte from remote
branch `research/local-gpu-candidate-triage-20260928`, tip
`8254993431f095c220f8080e7596cb0d9e6a9ae8`. It is a historical decision
snapshot, not the current GPU schedule or a result.

The note itself reports that no model load, fit, prediction, download, or
container mutation occurred. Its issue states were subsequently updated; read
the linked GitHub issues/PRs before any action. In particular, #5014 still
requires exclusive resource ownership and its latest archived v2 STOP/HOLD
does not authorize GPU work. This recovery did not run any GPU or model code.
