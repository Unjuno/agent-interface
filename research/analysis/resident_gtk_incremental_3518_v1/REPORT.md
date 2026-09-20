# Causal incremental resident-policy construction — #3518

**Decision:** `PASS_CONSTRUCTION_ONLY`; no GTK/X11 allocation was run.

## H/T/D/C/U

- **H:** A policy that consumes events one at a time can preserve causal action history, release after later revocation, refuse revocation-first and delayed stale input, and avoid duplicate rising-edge emissions. Explicit arrival-order `LAST_MESSAGE` and cumulative true-observation `MESSAGE_COUNT` controls are behaviorally distinguishable.
- **T:** Candidate files are `policies.py`, `test_policies.py`, and an independently written `audit_construction.py`. The candidate is a stateful event stepper; the audit launches it as a subprocess and compares action sequences to hard-coded expected rows without importing its policy functions. The matrix covers revoke-after-emit, revoke-before-observation, replacement before delayed old-generation input, stale false after a newer true observation, and duplicate true arrival.
- **D:** In OrbStack `agent-interface-3311-runtime-v2:20260920` (`sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`, linux/arm64), network disabled and source mounted read-only, `python3 -m unittest -v` passed 5/5 and `python3 audit_construction.py` passed 5/5 exact rows. Later revocation did not erase an earlier emission; it appended release. Revocation-first and stale/replaced inputs refused.
- **C:** Finite synthetic event traces only. Candidate control semantics are introduced for #3518 and do not redefine the prior allocation's controls. No GUI, model, user input, production runtime, or task-effect claim.
- **U:** Broader event schedules, independent adversarial audit, semantic alignment with the GTK fixture's observable cases, real GTK allocation, and production transfer remain open.

## Reproduction

From this directory, run:

```bash
python3 -m unittest -v
python3 audit_construction.py
```

For the reported container run, mount this directory read-only at `/src`, set working directory `/src`, pass `--network none`, and use the exact image digest above. The source SHA-256 values are recorded in the PR description.

This construction result does not clear #3511's resident-policy claim for merge. Any formal allocation must be separately frozen after expanded negative tests and GTK case-matrix review.
