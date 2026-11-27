# Native MCP CI failure baseline comparison — 2026-11-04

## Question

Does the PR's `native-mcp` CI failure come from the current Calc integration
change, or does the same test failure occur on its unchanged main base?

## Controlled local replay

Both revisions were mounted read-only into the same cached image
`agent-interface-xvfb-mcp:late-input-r19`
(`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`),
with network disabled, 2 CPUs, 4 GiB memory and swap, and 256 PIDs. The image
uses Python 3.11. Source revision was the only changed input:

- Current main base `cf3ddf2f8ef44f78fac3cfed78df2904aa596691`: exit 1.
- PR head `c516f080a30625a129c9b8ca930e526a121bef39`: exit 1.

Exact targeted command on both revisions:

```text
python3 -m unittest \
  runtime.cli_v1.test_mcp_server.PublicMCPTests.test_retained_image_can_be_omitted_without_changing_result_or_replaying \
  runtime.cli_v1.test_mcp_server.PublicMCPTests.test_strict_arguments_refuse_before_backend \
  runtime.cli_v1.test_post_dispatch_capture.PostDispatchCaptureTests.test_invalid_post_capture_rejects_before_session_or_input
```

The same three tests fail on both revisions with `AssertionError: Exception
not raised` / `AssertionError: ToolError not raised`. In the third test, the
invalid bool-as-int region is the failing subcase. This shows the targeted
failure predates the PR in this pinned Python 3.11 environment. It does not
explain the broader Python 3.12 GitHub job and does not make the CI check pass.

## PR check interpretation

The GitHub `native-mcp` check for PR head `c516f080a30625a129c9b8ca930e526a121bef39`
failed these same named tests. Its other integration checks were still in
progress when this record was written. Preserve the CI failure as a failure;
do not label this check green or infer it is harmless. Investigate runtime
validation semantics and the native CI report separately from the Calc
feature's Docker suite.

## Test contract correction on the PR branch

Inspection confirmed that `PublicArgumentMCP.call_tool` intentionally returns
an MCP `CallToolResult` with `isError=true` for schema failures; it does not
raise a local `Exception`/`ToolError` for these in-process calls. The three
tests had required exceptions, so their assertion form did not match the
implementation's protocol response. The PR now checks `isError`,
`status=invalid_request` or the schema-validation error, and still verifies no
backend/session dispatch, no input, and no operation. This preserves the
refusal and side-effect gates while matching the public result contract.

With this test-only correction, the same three tests pass in the pinned Docker
image in normal mode (3/3) and optimized mode (3/3), exit 0. The original
pre-correction failures remain described above as retained evidence; the new
CI run for the corrected head is the next full-suite check.
