# Host contention snapshot — migration pilot gate

Read-only Windows process inventory at 2026-10-02 found eight `wsl.exe` launchers for the same Ubuntu workload:

```text
/var/tmp/agent-interface-integrated-main
research/live_control/native_mcp_v1.py
--allocation-directory results-local/native-host-integration-03
--app calc-inkscape --seed 991315 --max-stages 24
```

These are shared, unknown-owner workers. They were not signaled, inspected internally, attached to, or modified. Because Issue #6389 requires no concurrent heavy workload for its first comparison, no native-vs-WSLc timing/RSS run was started. Prior memory/PSI was a single host snapshot only and is not comparative or workload attribution evidence.

## Gate

- native candidate=0; container candidate=0; independent migration auditor=0; retries=0.
- No candidate CPU-only workload was selected: local `research/analysis` scan found test modules but not a clearly established candidate/container command pair with a frozen input and independent replay audit.
- Re-open the pilot only after shared-worker ownership/clearance is established and a qualified CPU-only route is selected prospectively. Keep the GUI #6526 STOP and all previous #6389 HOLD conditions unchanged.
