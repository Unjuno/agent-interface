# Win32 supervised standard MCP bounded UNKNOWN under blocked recovery — R19

R19 is a one-shot local Windows trial through the public stdio-MCP caller,
frozen at source `9d0342e35aa2e0fd03f5c08f29b6c8bbf331fb47`. It holds one
injected Q-down callback for 4000 ms, beyond the observed 2975 ms cleanup
lifetime, with a 5500 ms self-release cap. It samples the exact producer PID and
creation time, same-call cancellation status, and release receipt.

This trial asks whether an unrecoverable blocked recovery helper transitions to
terminal `UNKNOWN` within 3500 ms while the hook callback remains held. The
probe suppresses the held Q-down when the callback returns, preventing the test
stimulus from leaving a key down if the recovery worker was retired. A passing
audit would establish bounded fail-closed status only; it would not establish
input release or recovery. It also requires the exact R19 task effect and owned
fixture/hook/foreground cleanup. No replay or rerun.

Only the user-authorized Windows PC and one owned fixture are used. No WSLc or
Docker allocation is used. Runtime `task_success` remains null.
