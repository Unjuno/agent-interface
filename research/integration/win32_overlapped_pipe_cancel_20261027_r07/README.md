# Win32 overlapped pipe cancellation R07

This fresh diagnostic tests a possible transport primitive after R06. A gated worker and separate non-reading peer ran inside an owned Windows Job Object. The worker used CPython `_winapi.WriteFile` with an overlapped operation on the pipe to send 8 MiB. The 200 ms wait returned `WAIT_TIMEOUT`; cancellation was requested, the completion event became signalled, and `GetOverlappedResult(False)` reported error 995 (`ERROR_OPERATION_ABORTED`) with zero bytes reported. The worker then retired its owned peer and exited; process inspection found neither PID remaining.

This is a single observed schedule, using a private CPython/Windows interface and arbitrary bytes rather than the supervisor protocol. It is not proof of an end-to-end deadline, absence of bytes already delivered to a peer, exact helper identity/retirement, or safe replay. The durable trace writes perturb timing. A real implementation must handle cancellation races and unconfirmed cancellation conservatively, preserve UNKNOWN custody, and cover reads, serialization and retirement separately. No GUI, game, model, native keyboard/mouse input, WSLc or Docker was used.

Exact source, environment, output, traces and hashes are retained. Rerunning requires a new output directory.
