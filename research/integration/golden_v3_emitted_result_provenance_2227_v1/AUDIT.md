# Independent source audit

The v3 source has one executable path: `main()` patches v2 globals and calls `previous.base.main()`; `run_live()` patches `previous.base.doctor` and calls `previous.run_live()`. The v2 writer calls `base.dump(out / "golden-report.json", report)` and sets schema `agent_interface_golden_desktop_live_v2`.

Thus the exact emitted boundary is v2's report, not a v3 result object. The only v3-specific transformation is appending openpyxl/et_xmlfile doctor checks and changing the doctor schema label to v2. There is no v3 report writer or v3 lifecycle/cleanup event emitter in the pinned source.

Disposition independently recomputed: HOLD_SOURCE_EMISSION_GAP.
