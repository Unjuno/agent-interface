# XDamage temporal-boundary v3 results — allocation HOLD

- Allocation: `xdamage-temporal-boundary-3935-v3-20260927-01`
- **Allocation disposition: `HOLD_PREREGISTRATION_PATH_IDENTITY`.** Do not treat this as a formal scientific PASS.
- Source commit: `9a27ffd5180ae8c4a77afa872e0f9f2ffb38f0ee` (frozen source, based on main `c1e6f24d259f96b4d4dbf211e83fcdf6b9e0a4dd`)
- Docker image ID: `sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4`
- Execution was local Docker, Linux/WSL2, `--network none`, 1 CPU, 2 GiB memory, no GPU.
- **Protocol deviation:** Issue #4900 required the exact output-path identities to be frozen on GitHub and read back before any X server/case. The two directories below were checked absent before use, but their identities were not included in the pre-run GitHub freeze. This provenance/preregistration requirement was missed. The paths are recorded here post hoc, not represented as preregistered:
  - Construction: `scratch/xdamage-v3-construction-01`
  - Formal: `scratch/xdamage-v3-formal-01`
- Therefore the independent raw-data audit passing does not upgrade this allocation to a scientific PASS. The one formal invocation is consumed; **no rerun/replacement under this allocation**.
- Construction raw audit: `PASS_CONSTRUCTION_PIPELINE`, 6/6 rows, zero audit errors.
- Formal runner: candidate complete, 8 sessions × 6 cases = 48/48 rows. Independent raw auditor disposition: `PASS_XDAMAGE_TEMPORAL_BOUNDARY_V3_SCOPED`; `audit_errors=[]`; 9 corruption controls rejected (8 required). These are preserved as technical audit findings only, under the allocation-level HOLD.
- Protocol unit tests: 7/7 pass.
- Formal ZIP SHA-256: `B220D1C470D3882D0B8F55558ABE6FB066E1C9B23CFD0A524F79802D04B9C824` (`FORMAL_EVIDENCE.zip`).
- Construction ZIP SHA-256: `EA89636BA125BC4324770C676ACCF0B4E8A25C40A8DAC9A391F7B1A7FC2CE44F` (`CONSTRUCTION_EVIDENCE.zip`).

| Case | n | XDamage observed | Endpoint forwarded |
|---|---:|---:|---:|
| QUIET | 8 | 0 | 0 |
| REPAINT_A | 8 | 8 | 0 |
| PERSIST_B | 8 | 8 | 8 |
| ABA_1PX | 8 | 8 | 0 |
| ABA_2X2 | 8 | 8 | 0 |
| ABA_8X8 | 8 | 8 | 0 |

The technical auditor's typed negative controls all remain `UNKNOWN` with `action_authority=false`. Raw RGB frames, per-case receipts, runner/auditor summaries, corruption-control outputs, and invocation marker are preserved in the ZIP evidence archives. This remains a scoped observation method, not a GUI/action-authority claim.

This corrected disposition supersedes the earlier `RESULTS.md` status at commit `17c24a3855bd03d33333c515c00607089af743be`; that earlier summary did not account for the output-path preregistration gap. Raw archives are unchanged.
