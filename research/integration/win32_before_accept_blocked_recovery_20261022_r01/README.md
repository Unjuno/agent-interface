# Win32 public recovery before DOWN acceptance — R01

Date: 2026-10-22. Source identity is recorded in `raw/results.jsonl`.

## H / T / D / C / U

- **H:** If the synchronous DOWN call blocks before acceptance, current public recovery may refuse because its post-call ledger and recovery flag have not yet been set; the original producer may then accept DOWN after recovery has already returned.
- **T:** Run current `Win32RuntimeSession.dispatch()` and `recover_input()` concurrently around an inert fake `user32`. Hold the first DOWN before the fake changes state; call public recovery; then admit the old DOWN and block its return to sample the interval before ordinary terminal cleanup. Run normal and optimized Python.
- **D:** This constructed schedule is observed if recovery returns `INPUT_RECOVERY_NOT_REQUIRED` with no UP and fake state neutral, followed by old DOWN acceptance while the old call remains blocked. The final terminal UP must restore fake neutrality after the old call returns.
- **C:** The barrier placement is imposed by the test double. Windows does not promise to block at this point, and the fake cannot establish native queue behavior.
- **U:** No claim about bounded native release, Windows ordering, physical key state, task effect, WSLc, or reliability.

## Result

`raw/results.jsonl` retains the normal and optimized runs, monotonic timing and source blob IDs. Both runs exercise the real public session recovery method. While the fake DOWN is blocked before acceptance, `recover_input()` refuses with `INPUT_RECOVERY_NOT_REQUIRED`, `release_attempted=false`, no API events, and no held-key ledger entry. The old DOWN is accepted after recovery returns and the fake reports CTRL down while `SendInput` is still blocked before return. After it resumes, the operation's ordinary terminal UP leaves the final fake state neutral.

This confirms the source-derived pre-acceptance schedule for the injected fake. It complements, but does not replace, the separate accepted-before-return packet. It shows why recovery cannot be considered completed merely because a public method quickly refused. It does not prove Windows can or does exhibit this exact schedule. The overall result remains `UNKNOWN` until producer fencing, independent native state readback, and a fresh-target task effect are qualified.

No WSLc/Docker allocation, native API, desktop input, or application task effect was used. The first accepted-before-return outcome remains immutable.

## Reproduction

From the repository root:

```powershell
py -3.13 research/integration/win32_before_accept_blocked_recovery_20261022_r01/probe.py --mode normal --output research/integration/win32_before_accept_blocked_recovery_20261022_r01/raw/results.jsonl
py -3.13 -O research/integration/win32_before_accept_blocked_recovery_20261022_r01/probe.py --mode optimized --output research/integration/win32_before_accept_blocked_recovery_20261022_r01/raw/results.jsonl
py -3.13 research/integration/win32_before_accept_blocked_recovery_20261022_r01/audit.py --input research/integration/win32_before_accept_blocked_recovery_20261022_r01/raw/results.jsonl --output research/integration/win32_before_accept_blocked_recovery_20261022_r01/raw/audit.json
```
