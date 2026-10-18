# Blocked owner I/O with independent X11 release A11

**Result:** `PASS_XVFB_BLOCKED_OWNER_RELEASE_SCOPED` — 8/8 trials passed the frozen Xvfb gates. The run used the pinned Python image and a fresh WSLc container after an empty-running-container preflight; the exact container ID is now absent from both all-container and running-container queries. Conditions, source hash, allocation details, exact argv, raw output, and a raw-derived audit summary are retained here.

For every trial, the task KeyPress reached the focused Xvfb window and key-down was still present at the disconnect fence. The owner's XSync remained blocked while 32 server-to-owner reply bytes were withheld. After terminating/reaping the owner, an independent XRes observer saw that exact owner client disappear, then a separate X connection delivered KeyRelease. Key-up was confirmed immediately and after 50 ms. There were no proxy errors. Owner retirement measured 1.159–3.350 ms, XRes disconnect observation 1.640–3.806 ms, and key-up readback 56.126–56.776 ms in this fixture.

- Conditions and frozen probe: [`conditions.json`](conditions.json), [`probe.py`](probe.py)
- Machine-derived gate summary: [`audit-summary.json`](audit-summary.json)
- Run receipt: [`run-result.json`](run-result.json)
- Raw WSLc output: [`raw/wslc-run-raw.log.gz`](raw/wslc-run-raw.log.gz), compressed SHA-256 `cf178b06c76d811d8d4fc293f9f7c27f1f8f8449f99e3fe5f769eba1fbb963e1`; uncompressed SHA-256 `fd0ef622657e20e69c37f87b67e2298b42ca94bc84fba1f98f62f66b43b4f493`. The gzip round-trip hash was verified against the retained raw log.
- WSLc post-run cleanup: [`raw/post-run-container-check.json`](raw/post-run-container-check.json) records successful all-container and running-container queries with the exact A11 ID absent.

## Local verification

On Windows CPython 3.13.14 with `mcp==1.30.0`, `python-xlib==0.33`, and
`Pillow==13.0.0`, the spawn-safe [`run_local_validation.py`](run_local_validation.py)
ran 107 selected guarded-MCP tests successfully in normal and optimized (`-O`)
modes. The same tests ran from one fixed venv so spawned owner and MCP child
processes used the same interpreter and dependencies. One unrelated packaging
test, `test_portable_stdio_runs_outside_checkout`, was excluded because this
frozen branch does not contain `runtime.distribution_v2`; it is not counted as
a pass. Compressed raw unittest outputs are retained in
[`raw/local-selected-tests-normal.log.gz`](raw/local-selected-tests-normal.log.gz)
and [`raw/local-selected-tests-optimized.log.gz`](raw/local-selected-tests-optimized.log.gz).

The deterministic reply-gate regression from A10 also passes in normal and `-O`
mode: [`normal`](raw/reply-gate-check-normal.txt) and
[`optimized`](raw/reply-gate-check-optimized.txt). This verifies the local
proxy race check, not the live Xvfb result by itself.

This is bounded Xvfb evidence for one failure topology: the control owner is stuck waiting for an XSync reply while the X server can still serve an independent observer and KeyRelease client. It supports owner-process retirement followed by separately issued release in that scope. It does not show that terminating a process alone released the key: key-down remained present at the disconnect fence, and release required the independent KeyRelease. It does not establish behavior on a physical desktop, XWayland, a permanently unresponsive X server, or the standard guarded-MCP caller, nor independently verified real-app task success, general bounded recovery, timing/economics, or matched reliability. A01–A10 remain immutable; this A11 result does not upgrade their outcomes.
