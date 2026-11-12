# MAP01 independent task oracle

This research callback plugs into `create_server` through
`supervised_win32_task_oracle`. It is not enabled by the default CLI and never
dispatches inputs. Its scope is the frozen 1520x825 MAP01 HUD and an ammo
transition from 50 to 49, not completion of MAP01 or general OCR.

The callback joins the terminal action's call ID, operation ID and generation
with a trusted experiment's baseline and release readback, then requests a new
capture from the injected server-side capture adapter. A palette-only change
does not count as an ammo decrement. Unknown geometry, generation, baseline or
classification remains UNKNOWN. Runtime action completion and recovery are
separate from this task-effect result.

## D16 capture-time correction

The earlier private research callback accepted stale and future capture
metadata because it checked only end >= start and stamped a fresh receipt.
An offline probe changed only timestamps and reproduced both false accepts.
This does not establish that a historical native capture was stale.

The callback now requires strict integer timestamps satisfying:

`request <= capture start <= capture end <= capture return <= receipt`

It preserves capture timing in `oracle-receipt.json`. This validates the
trusted adapter's reported timestamps; it cannot detect an adapter that lies
about the age of its pixels. The baseline and templates remain trusted
experiment inputs, not untrusted arbitrary caller content.

## Local validation

From the repository root, with Pillow and the runtime dependencies installed:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m unittest discover -s research/integration/map01_numeric_ammo_oracle_20261111 -p 'test_*oracle.py'
```

The 13 tests cover numeric positive and palette negative controls, geometry,
identity/release refusal, seven malformed capture-time cases, and the public
MCP recovered-action verification path. No live input is dispatched by these
tests. A fresh native experiment is still required to establish the corrected
callback's live result; no performance or reliability improvement is claimed.

The templates are cropped historical research fixtures. Their original frame
and output hashes are retained in `oracle-fixture-provenance.json`; the full
private experiment packets are not published by this change.
