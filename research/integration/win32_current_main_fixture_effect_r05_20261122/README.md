# Current-main Win32 standard-caller fixture R05

Status: `PASS_SCOPED_FIXTURE_EFFECT`. This is a third fresh scripted fixture success after R03/R04. It is not a reliability estimate, recovery run, provider comparison, MAP01 result, or Research Preview acceptance.

## Frozen setup and target custody

- Tested repository main: `ee14863bec0c7a222bec4d96300162afde61cf82`.
- The R04 `fixture_app.py` and `live_probe.py` source blobs were materialized byte-for-byte from that commit and hashed in `conditions.json`.
- A read-only foreground identity probe was added before dispatch to enforce the frozen exact-window gate; its source is included in the packet manifest.
- Host: Windows 10 build 26300, CPython 3.11.9, MCP 1.30.0.
- Fresh fixture: PID 25796, HWND 35654768, title `Agent Interface Win32 Fixture`.
- CUA returned exactly one matching window. It was activated, visually inspected, and a separate Win32 query immediately before dispatch verified foreground HWND, PID and title. The public observation then returned a matching target generation.
- One action only; no retry. The exact caller program was focus, one A key chord, `release_all`.

## Result

- Public action status `completed`, call `2b50767aa60c49b18f55c6e1a4a59cdd`, operation `ad31649af5a34b66856b3384fbe16da5`.
- `release_confirmed=true`; empty down/unknown key and button sets; release key-up returned; independent neutral readback passed.
- The 2 s late-input horizon sampled 77 times; maximum observed gap was 32 ms against a 100 ms bound, with no validation error.
- The separate fixture oracle recorded one accepted A key-down, its key-up, and text `a` after 6,015 ms. This fell 3,953 ms after the neutral-horizon readback ended.
- Public `task_success` stayed `null`, and replay remained denied. Thus the external fixture effect is retained as fact, but the task-effect handoff into the public result remains unresolved.
- No recovery was needed. `interface_close` returned closed with zero unresolved calls. Its `release_confirmed=false` is consistent with the current API docstring: close issues no new input release; inspect the retained action/cancellation receipt. The action receipt itself has the verified release above.
- After terminal custody, Computer Use sent Alt+F4 to the exact run-owned HWND; the CUA window inventory showed none remaining, and a later process query found no fixture Python process.
- The three focused Win32 backend-composition, producer, and MCP-composition suites pass 27/27 normally and 27/27 under `-O` on the same main and CPython 3.11.9. Complete logs and summary are under `raw/regression-*.log` and `raw/regression-summary.json`.

## Limits and retained evidence

The sample has no model/provider calls or efficiency measurements. Three scripted fixture successes still do not establish a population reliability rate. The independent task oracle is not yet joined to public `task_success`; matched economics and live MAP01 remain open.

The frozen conditions, exact source, raw MCP journals/reports/observation, task events/effect, foreground proof, cleanup receipt and SHA-256 manifest are retained under this directory. `raw/source-custody-audit.json` preserves an initial false mismatch caused by using Git's configured clean filter, then the corrected no-filter/blob-byte comparison that passed. Verify the packet with `sha256sum --check SHA256SUMS` from this directory.
