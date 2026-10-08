# Issue #6526 A03 — deadline-audit timing HOLD

Allocation `OBSERVATION-INTERVENTION-6526-A03-DEADLINE-AUDIT-ONLY-20261003-01` is a post-hoc audit-only successor to A02. It ran no candidate (0 invocations) and one raw-only corrective auditor (exit 0). A02 raw, original audit, and original report are preserved unchanged.

## Finding

Disposition: `HOLD_AUDIT_TIMING`; hypothesis classification: `NOT_EVALUATED_AUDIT_TIMING_GATE_UNRESOLVED`.

All 180 actual `snapshot_ns` values were later than their nominal deadlines (0 exact-time samples); observed lag ranged 0.046112–46.349356 ms. The original A02 auditor had no frozen maximum snapshot-lateness gate and reported all six arm/schedule cells as 0/30 misses, `H_FAIL_SCOPED`.

The corrective review found one direct contradiction: trial `b05-sensitive-screenshot` persisted its expected effect 12.370083 ms after the nominal deadline, but its clock-thread snapshot occurred 12.428198 ms after that deadline and saw the now-existing file. The original auditor therefore treated an after-deadline effect as present at deadline. The A02 preregistration had no nonzero sampling-lateness tolerance; this review does not invent one after seeing outcomes. The exact-deadline oracle gate is unresolved, so neither a positive nor a negative H classification is warranted.

For transparent descriptive reconstruction only, raw `persisted_ns <= deadline_ns` gives one sensitive SCREENSHOT miss (1/30) and zero misses in the other five cells. This event-time reconstruction is not the preregistered independent punctual-oracle result and does not override HOLD. A01 `STOP_AUDIT_ERRORS` and A02's original files remain unchanged; A02's original H_FAIL label is retained as the historical first-auditor output, not the current accepted scientific disposition.

## H/T/D/C/U and custody

- **H:** Not evaluated; exact-deadline timing cannot be established from A02's sampling design.
- **T:** Audit-only read of A02's frozen trial plan, 365-file output archive, app event stream, deadline/effect records, candidate receipt, and original auditor JSON. Candidate 0; corrective auditor 1; retry 0.
- **D:** 180 expected IDs/order and action/deadline records reconstructed, zero structural errors. Original auditor result was `H_FAIL_SCOPED`, but the separate timing review returned `HOLD_AUDIT_TIMING`; one late effect was observed only after its nominal deadline.
- **C:** Shared-host thread scheduling delayed the nominally independent sampler. The app's atomic-persistence timestamp provides a descriptive event-time bound but cannot retroactively make the sampler punctual.
- **U:** Same synthetic Tk/Xvfb fixture, one ARM64 OrbStack VM/host; no real application, model, human, production, safety, or causal-generalization evidence.

The reviewer source/tests and pre-audit freeze are in this directory. `results/a03-review.json` is the auditor output; `results/SHA256SUMS.txt` covers retained outputs. A02 input identities are bound in `FREEZE.json`; the full A02 raw archive remains at its original path.

## Next boundary

Do not rerun A02 or reinterpret the late sample as on-time. Any fresh candidate study needs a prospective deadline-observation contract with a justified and validated sampling-lateness bound or a suitably timestamped independent event source, plus a separately frozen allocation. This audit-only HOLD does not authorize that candidate allocation.
