# Calc input-guard composition prototype (offline)

Current-main source base `251c4199bd5cc2bfdc995322eaf9f32576b7ffd4`; predecessor `runtime/results/calc-owner-composition-01` is unchanged. The baseline transcript records 51 tests with one failure and three errors caused in part by an old bridge fixture missing the current guard entry point.

The candidate connects the compiled and ordinary Save paths to the existing input guard, with fresh-source association and frozen OCR-approved cell pixels. Fake-X tests exercise normal, wrong/unknown OCR, changed pixels while Ctrl is held, and preservation of the completed prefix. A separate test uses the actual NativeHandleBridge with a Fake X transport and simulated OCR evidence: the changed cell stops the subsequent key and its release receipt is verified. The candidate remains trusted local research code; the legacy monkeypatch helpers remain in `save_guard.py` for comparison and are not used by these two candidate paths.

The result is not a live Calc, public MCP, independent persistence, real display input, model-token, latency or reliability result. Ordinary and compiled test doubles do not prove process cleanup or general target identity. Additional composed native tests, independent scoring and a fresh prospectively fixed allocation are required. `results.json` and test logs record the commands and results; no historic allocation was rerun.

Host mount paths in published command records are replaced with placeholders; original baseline command remains in the local work directory.
