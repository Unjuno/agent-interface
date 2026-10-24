# R49 result

Disposition: `PASS_SCOPED` for one paired native-Windows supervised-caller fixture sequence. The combined audit passed 13/13; phase 1 passed the frozen strict release gate 11/11 and phase 2 started only after that pass. R49 is one independent replication of R48, not a reliability estimate.

Phase 1 used one public dispatch and one public cancel. The cancel response took 1.7481 ms. The Q-up callback stayed held for 1,410.2225 ms after the cancel response, above the preregistered 1,400 ms planned interval and 1,250 ms minimum. The exact call remained pending across 90 polls. The same-generation sampler recorded 74 eligible Q-up samples while the callback was held; recovery Q-up `SendInput` returned after 311.1253 ms. The sampler exited normally after 600 samples.

Only after the strict phase-1 gate passed, phase 2 used a new fixture process/window, target generation, call, operation, task token and oracle ID. The independent server oracle verified the exact fixture effect (`clicked=true`, `saved=true`, and the frozen R49 token). The completed call had a verified neutral release receipt and separate neutral readback. The effect-file write-return to oracle read-start interval was 220.5783 ms; this is a fixture/file observation interval, not physical input-to-effect or durable-storage latency.

Both phase processes and the fixture exited with code 0, and foreground restoration passed. The phase-2 session-close record reports `release_confirmed=false`, while the completed action itself has `release_confirmed=true`, neutral state witnesses, no unresolved calls and `replay_allowed=false`. Runtime-integrated `task_success` remains null; the success claim belongs only to the separately bound external oracle.

The run used Python 3.13.14 on current-main commit `eb0c4b81954369fcd57198150ebf59a9c7db76d5`. The input-free preflight passed all 13 checks, including R48 predecessor hashes, current runtime source hashes, MCP SDK, Win32 and timing requirements. Computer Use activated only each unique owned fixture after inspecting its screenshot; the runner independently verified the foreground HWND and process owner.

This was a user-authorized native-Windows PC attempt. It used no WSLc or Docker. WSLc remains STOP/HOLD because the shared session owner is unresolved. R49 does not establish MAP01 or real-app transfer, matched efficiency, model/token accounting, broad reliability, hard real-time behavior, or WSLc application control. Preserve the raw packet independently; do not replay this one-shot attempt.

The local private evidence copy is verified by the original `SHA256SUMS`; the sanitized public packet is verified by `SHA256SUMS_PUBLIC_R01`. `PUBLICATION_CUSTODY.json` records the path/host redaction counts and confirms the raw trial outcome was unchanged.
