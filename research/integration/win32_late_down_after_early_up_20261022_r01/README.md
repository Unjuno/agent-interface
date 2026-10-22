# Win32 late-DOWN-after-early-UP counterexample — R01

Date: 2026-10-22. Source under test: current checkout commit recorded in `raw/results.jsonl`.

## H / T / D / C / U

- **H:** Submitting a compensating UP from a second sender before retiring an old producer does not guarantee neutral state if the old producer can still accept a delayed DOWN.
- **T:** Exercise the actual `Win32RuntimeSession.dispatch()` and `Win32Backend` with a deterministic inert `user32` fake. Block the first DOWN before acceptance; let a counterfactual recovery sender submit UP; then accept the old DOWN and hold its call before return so fake key state can be sampled before the original program's terminal cleanup. Run normal and optimized Python.
- **D:** The counterexample is established for this injected schedule if the trace is UP, old DOWN, with fake key state down between old DOWN acceptance and return. It is limited to the fake schedule. The test must also retain the later ordinary terminal UP and neutral final fake state.
- **C:** This schedule is imposed by the test double; Windows `SendInput` queue behavior, API blocking, physical key state, and process termination are not modeled.
- **U:** The result does not establish native release timing, Windows event ordering, target effect, WSLc behavior, or reliability.

## Result

`raw/results.jsonl` contains one normal and one optimized run with monotonic event timestamps and exact source blob IDs. Both modes must show the early UP followed by the old producer's late DOWN while its API call is still blocked, then the original dispatch's ordinary terminal UP after the call is released. The record is append-only and hashed in `SHA256SUMS`.

This is a counterexample to “a second UP alone fences a producer.” It is not a new runtime implementation or a Windows qualification. The current public `Win32RuntimeSession.recover_input()` refuses while its recovery flag is false; the early UP is intentionally submitted directly by the inert test sender to model an unsafe proposed shortcut. A qualified recovery design still needs confirmed producer retirement or an independently enforced generation/deadline fence, platform-state readback, and separate fresh-target task-effect verification.

No real input, WSLc/Docker command, container/image RPC, or new resource allocation is used. The earlier accepted-before-return R01 packet is unchanged.

## Reproduction

From the repository root:

```powershell
py -3.13 research/integration/win32_late_down_after_early_up_20261022_r01/probe.py --mode normal --output research/integration/win32_late_down_after_early_up_20261022_r01/raw/results.jsonl
py -3.13 -O research/integration/win32_late_down_after_early_up_20261022_r01/probe.py --mode optimized --output research/integration/win32_late_down_after_early_up_20261022_r01/raw/results.jsonl
py -3.13 research/integration/win32_late_down_after_early_up_20261022_r01/audit.py --input research/integration/win32_late_down_after_early_up_20261022_r01/raw/results.jsonl --output research/integration/win32_late_down_after_early_up_20261022_r01/raw/audit.json
```
