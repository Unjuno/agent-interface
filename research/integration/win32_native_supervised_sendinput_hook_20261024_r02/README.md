# Native Win32 process-retirement and SendInput recovery — R02

**Disposition: `UNKNOWN` / `ABORTED_BEFORE_PRODUCER`.** The one-shot runner created the owned EDIT target and bound the current HWND generation, then stopped while constructing the cancellation supervisor: the recovery helper's ready receipt included `pid` and `ready_ns`, while the supervisor requires the exact two-field receipt `{"status":"ready","helper":"recovery"}`. No producer was started, no hook was installed, and no input was sent. The fixture was destroyed and the prior foreground window restored. The immutable raw result and read-only audit are retained below; neither supports an input-release result.

- [`raw.json`](raw.json), SHA-256 `c75cad766b7e2aa87afbc05adab03667ecf1dae80877bab14632fd96cb57c012`
- [`audit.json`](audit.json): `UNKNOWN`; frozen conditions and source hashes match.
- [`audit_construction_failure.json`](audit_construction_failure.json) and [`audit-failed-r01.py`](audit-failed-r01.py): preserve an earlier auditor path error and the corrected independent auditor.
- [`construction_failure.json`](construction_failure.json) in R01 preserves the earlier import-path failure; R01 did not reach the OS or emit input.

R03 is a new, separately frozen construction that changes only the readiness receipt to the exact contract. It must remain a one-shot attempt; R02 is not rerun.

## Scientific scope

The question is whether a disposable Win32 producer blocked inside a real `SendInput` call by a `WH_KEYBOARD_LL` callback can be retired, followed by one prestarted recovery process issuing UP and an independent state readback, all within fixed deadlines. It uses one visible, owned EDIT fixture and binds operations to the observed target generation. F13 has no task oracle, so `task_success` remains null. Even a PASS is a single native schedule and does not qualify the standard MCP caller, MAP01, or broad reliability.

## Frozen conditions and evidence

`conditions.json` and `probe.py` are immutable R02 source bindings. `raw.json` records process, hook, API, supervisor, recovery, observation, horizon, and cleanup events. `audit.py` / `audit.json` independently check hashes, ordering, timing, state and cleanup. R02 produced no native input; it cannot be interpreted as an experiment PASS or FAIL.
