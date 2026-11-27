# S04 preparation

Registered at 2026-10-23T23:26:46.9789920Z before any WSLc session start, image pull, or container start. Source commit `64543a8ac5b01ac8acff3910e4fc2e0458276f6c`. The harness creates a new session through `Microsoft.WSL.Containers` v3.0.3 with globally unique name `agent-interface-wslc-s04-18b5966286de4f9486eecc30b90059eb` and absent storage path `D:\CodexData\Temp\agent-interface-wslc-s04-18b5966286de4f9486eecc30b90059eb`. The name contains no credentials and is visible machine-wide while active.

One pull of `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` and one run are allowed. The container network mode is None; image acquisition uses host-side registry access. Session limits are 1 CPU and 1024MB. A read-only mounted disposable sentinel is read, then a write is attempted and must fail with EROFS. Exact container/image cleanup precedes session termination. Storage removal is allowed only after successful termination.

Any timeout or ambiguous result ends S04 as HOLD/UNKNOWN; no retry. This tests WSLc API session/container setup and bind-mount behavior only. It does not establish computer control, GUI input release, application response, bounded recovery, or task effect.
