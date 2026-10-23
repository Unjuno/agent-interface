# Win32 public MCP synthetic cancellation and independent task-effect composition — R02

R02 extends the R01 synthetic public-caller packet with an independent task-effect result. On source commit `7f5dd3a35a6c1ea2e2ac23c4a43e71f43230f8cb`, the public MCP route bound and rechecked a synthetic target generation, admitted a gated producer child, observed a synthetic completion event in a separate spawned oracle process, then canceled the producer and composed separate spawned recovery and neutral-state observation.

The public oracle tool returned a generation-bound task-effect receipt with `task_success=true`. The cancellation response kept `task_success=null`; the retained action remained `running`; the terminal cancellation record reported synthetic recovery/readback separately. The test also verifies that the oracle tool is absent when no oracle is injected.

The 23 focused Win32 adapter/composition/cancellation tests passed in normal and optimized CPython 3.11.9 (23/23 each). Exact command output is in [`raw/normal.log`](raw/normal.log) and [`raw/optimized.log`](raw/optimized.log). Conditions and source fingerprints are in [`CONDITIONS.json`](CONDITIONS.json).

This is synthetic process-ordering evidence only. It does not exercise native `SendInput`, a live HWND/application, physical input state, producer-fence behavior in Windows, late-DOWN exclusion, exclusive desktop input ownership, MAP01, a matched efficiency comparison, or reliability. The oracle scores an injected event, not an application-backed task. No WSLc allocation, Docker use, or native input occurred. Keep Issue #7924 STOP/HOLD unchanged.
