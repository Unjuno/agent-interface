# R11 supervised Fake observation injection seam

R10 produced a retained orphan report for an `interface_observe` call against fixture HWND 123 with `Win32BackendError('invalid HWND for target fixture')`, despite the lifecycle test intending to patch `runtime.cli_v1.mcp_server.observe`. The report states `input_dispatched=false` and owner `call_count=0`, but Fake isolation for that cohort is unproven.

This minimal test creates the same `supervised-win32` server with the standard Fake owner/producer factories, patches the module observer to return a unique marker, and directly awaits one `interface_observe` call. It asserts the fake callback is invoked once and the unique marker is returned. If the test reaches Win32 instead, preserve the raw failure and stop further lifecycle trials until repaired. One normal and one `-O`; no retries.
