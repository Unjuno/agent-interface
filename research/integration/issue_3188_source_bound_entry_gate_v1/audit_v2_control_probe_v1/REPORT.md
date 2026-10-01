# Issue #3188 audit-v2 control-schema mutation probe

## H / T / D / C / U

- **H:** The post-outcome independent audit-v2 may accept malformed or semantically altered negative-control rows because its control validation checks names and HOLD decisions but does not bind every control's exact Boolean fields or reject non-Boolean field types.
- **T:** Read the immutable formal-02 raw and exact frozen candidate/auditor sources from base `eca4bcc1ee839b80442397e27f238c97d6dd6bb4`. Verify all four SHA-256 values before running. Invoke the exact `independent_audit_v2.py` function on the unchanged raw and on two in-memory-only JSON mutations. Never write to `raw.json`.
- **D:** `GAP_REPRODUCED` iff all four identities match, baseline audit-v2 returns `PASS_INDEPENDENT_AUDIT`, both mutation copies also return `PASS_INDEPENDENT_AUDIT` with no errors, and the on-disk formal raw hash is unchanged. A hash mismatch is STOP; an audit rejection of either exact mutation means this specific gap was not reproduced.
- **C:** Host CPython 3.12.10 process; no game, model, GUI, X11, input, network call, or Docker/OrbStack container. Formal result files are read-only inputs; mutations are only Python in-memory objects.
- **U:** Finite audit characterization only. The two accepted mutations do not revise, replace, or upgrade formal-02's `HOLD_FROZEN_AUDITOR_DEFECT`, and do not prove general auditor unsoundness.

## Frozen identities and observation

- Candidate `run.py`: `e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822`
- Candidate `audit.py`: `72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d`
- Independent auditor v2: `b0785c9008f4873502be7fc90ba259b939fa1662fbd0efb89aff65c38b799d3e`
- Formal-02 raw before and after: `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`

Observed on Windows CPython 3.12.10 using the committed probe command against an isolated scratch copy: baseline `PASS_INDEPENDENT_AUDIT`, errors `[]`; final disposition `GAP_REPRODUCED`, process exit 0. The normalized JSON outcome is retained in `RESULT.json`.

| In-memory mutation | v2 outcome | Errors |
|---|---|---|
| For control `missing_receipt`, set `terminal_integrity=true` and `arm_bound_audit=false`, preserving the HOLD decision | `PASS_INDEPENDENT_AUDIT` | none |
| Replace that control's JSON Boolean `false` with integer `0` | `PASS_INDEPENDENT_AUDIT` | none |

Both controls still have a HOLD decision, but the first no longer represents the named missing-receipt condition. The second violates the declared Boolean field type. The unchanged v2 checks the control's name and final HOLD status but does not verify the exact per-control field vector or require `type(value) is bool` for controls.

The probe source is `probe.py` (SHA-256 `c0a7f9694330f1d00a4c448b92569f6d8aff78104ee1aa5ff4204dcbd9ca2c4c`); run from a complete checkout with:

```sh
python research/integration/issue_3188_source_bound_entry_gate_v1/audit_v2_control_probe_v1/probe.py --repo-root .
```

Expected probe disposition on the frozen base is `GAP_REPRODUCED`. The formal allocation outcome remains exactly as retained. Docker Desktop's service was observed Stopped/Manual and `docker info` did not return server metadata during this continuation; therefore no container result is claimed. This probe is useful host evidence, not the separate-container validation gate.
