# Public stdio MCP live Win32 effect R01

This packet uses the standard `runtime.cli_v1.mcp_server` stdio process in
one-shot mode and the public `interface_observe` / `interface_dispatch` tools.
Its sole target is a fresh Agent Interface fixture process created by the
probe. The fixture window is visible and may briefly receive foreground focus;
the program sends a fixed click, short text, Ctrl+S, a final observation and
`release_all`. No other target is configured.

The fixture's effect JSON and event journal are read independently after the
MCP call. PASS requires exact saved contents, exactly one save event, the exact
number of character events and a verified final release receipt with no
unknown/down inputs. Timeout or uncertainty is retained; dispatch is never
replayed. The complete conditions and auditor are in this directory.

This experiment does not exercise the synthetic `guarded-win32` owner, target
generation at admission, blocked-I/O cancellation, supervisor recovery,
provider/model use, MAP01, or matched efficiency/reliability. One successful
one-shot does not prove reliability or bounded release.

## R01 outcome and integration repair

The frozen live attempt is `FAIL_OR_UNKNOWN` (auditor 7/11). Public
`interface_observe` returned `observation_failed`; the single public
`interface_dispatch` returned `runtime_failed` with
`ValueError('CAPTURE_ARTIFACTS_UNSUPPORTED')`. Source inspection found that
`runtime/cli_v1/api.py` configures the per-call image directory before calling
the session dispatch, but the Win32 backend did not implement
`configure_capture_artifacts`. Therefore the API stopped before
`session.dispatch`, and the fixture journal contains only `ready`: there were
zero character and save events, no effect file, and no release attempt to
score. The fixture process exited cleanly; target identity before/after was
unchanged. The raw response and failed frozen audit are preserved unchanged.

The repair adds dependency-free Win32 PNG artifact output from the exact
top-down GDI BGRX capture, preserving raw and PNG hashes and capture metadata.
The read-only observation regression verifies saved PNG bytes, decoded pixels,
chunk CRCs and no input side effects. The final focused suite passes 28/28 in
normal and optimized Python, and the full CLI/API suite from CI passes 131/131
(7 platform skips) in both modes. Initial repair-suite runs failed old
assertions that required supported artifact requests to refuse; those logs are
retained. The first PNG implementation relied on Pillow, which was absent from
CI on all three OSes; the CI failures prompted a standard-library encoder and
are preserved in the CI logs. R01 remains a failure. Separate R02 and R03
results are in their own packets.

The standard `runtime.cli_v1.test_mcp_server` suite also passes 24/24 in normal
and optimized Python after expanding this sparse checkout to include its
portable runtime source. Two earlier suite invocations stopped on missing
`runtime/host_v1` and `runtime/backends/quartz_v1` files; both setup logs are
retained and neither represents a product test failure.
