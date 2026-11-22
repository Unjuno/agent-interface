# A01 result: turn/steer same-turn observation forwarding

Disposition: `STOP_PENDING_WINDOW_INVALID`.

The single frozen candidate run used `codex-cli 0.146.1`, a temporary `CODEX_HOME` and `HOME`, analytics disabled, removed API credential and proxy variables, and a Responses mock bound only to `127.0.0.1`. `turn/steer` was accepted with the same turn ID as `turn/start`. The second captured Responses request contained the exact fixed observation text and the exact retained seq=200 PNG data URL. The turn completed and the mock recorded no server errors.

The timing control failed: the interval from the steer acknowledgement to releasing response 1 measured 4,004,277,167 ns, outside the frozen 1.9–2.2 second validity band. Request 2 arrived after response 1 completed. Since the bounded pending-window condition was invalid, this run does not support a valid `FAIL_STEER_QUEUED` conclusion and cannot establish preemptive forwarding. The candidate was not rerun.

The independent audit passed integrity and returned exit 0. The candidate returned exit 0. The detailed request and timestamps are retained in `candidate.stdout`; candidate stderr and exit code are retained alongside it. The corrected candidate source now starts the fixed deadline immediately after steer acknowledgement, but differs from the one-shot source hash and therefore was not executed. A fresh, separately frozen A02 would be required to test that correction.

This is a loopback protocol construction test only. It provides no real model inference, UI/game input, threat exposure, useful reaction, release/recovery, ammo/progress, terminal result, or MAP01 evidence, and it grants no live-game allocation.
