# R48 result

Disposition: `PASS_SCOPED` for one paired native-Windows supervised-caller fixture sequence. The combined audit passed 13/13; phase 1 passed the frozen strict release gate 11/11, and phase 2 started only after that gate. This is one independent replication of R47, not a reliability estimate.

Phase 1 used one public dispatch and one public cancel. The Q-up callback remained held for 1,405.5526 ms after the cancel response, exceeding the frozen 1,400 ms planned interval and 1,250 ms minimum. The exact call remained pending across 89 polls. The same-generation independent sampler observed 74 eligible Q-up samples while the callback was held; the recovery Q-up `SendInput` returned after 312.2387 ms. The sampler exited normally after 598 samples. The strict release audit passed all 11 checks.

After phase-1 cleanup, phase 2 used a new fixture process/window, target generation, call, operation, task token and oracle ID. The server-side oracle verified the exact fixture effect (`clicked=true`, `saved=true`, and the frozen R48 token). The completed call had a verified neutral release receipt and a separate neutral readback. The effect-file write-return to the independent oracle read-start interval was 268.4095 ms; this is a fixture/file observation interval, not physical input-to-effect or durable-storage latency.

Both phase processes and the fixture exited with code 0; foreground restoration passed. The phase-2 session close record reports `release_confirmed=false`, while the completed action itself has `release_confirmed=true`, neutral state witnesses, no unresolved calls and `replay_allowed=false`. Runtime-integrated `task_success` remains null; the success claim belongs only to the separately bound external oracle.

Conditions and source were frozen against current-main commit `58bf2b2268d315179d248f00f2fa5da7e4a1d5f8`. Python 3.13.14 preflight passed all 13 checks before input; all four R47 predecessor hashes and all six runtime source hashes matched. Computer Use activated only each uniquely identified, newly created owned fixture and inspected its screenshot before the runner independently confirmed the foreground HWND and process owner.

This was a user-authorized native-Windows PC attempt. It used no WSLc or Docker. WSLc remains STOP/HOLD because the shared session owner is unresolved. R48 does not establish MAP01 or real-app transfer, efficiency, matched model/token accounting, broad reliability, hard real-time behavior, or WSLc application control. Preserve its raw packet independently; do not replay this one-shot attempt.

The local private evidence copy is verified by the original `SHA256SUMS`; the sanitized public packet is verified by `SHA256SUMS_PUBLIC_R01`. `PUBLICATION_CUSTODY.json` records the path/host redaction counts and confirms that the raw trial outcome was not changed.
