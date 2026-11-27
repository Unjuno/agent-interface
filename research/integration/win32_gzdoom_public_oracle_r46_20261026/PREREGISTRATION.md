# R46: GZDoom public task-effect oracle integration

Question: can a server-configured independent oracle classify the pre-registered visible W-forward effect on one fresh GZDoom MAP01 generation, after the standard caller has confirmed terminal release?

Claim ceiling: task effect means a strict >5% changed-pixel fraction in the upper 80% of same-generation public screen captures. It does not mean MAP01 completion. One fresh process, one dispatch, one observation pair, one `interface_verify_task` call; no retries, replay, recovery, WSLc, Docker, or model/provider calls. Preserve old UNKNOWN processes 21660, 6696, and 60320.

Preconditions: freeze hashes for the runner, task oracle wrapper, runtime checkout and assets; verify existing GZDoom PIDs and HWNDs exactly; start only a fresh owned process; require user-visible exact-window CUA observation before dispatch. Use one 600 ms scan-code W action under a 30 s lease and the supported 10 s response wait. If action completion, same-generation release/readback, or the post-action public observation is unproven, stop and retain UNKNOWN. Close only the exact fresh HWND after release and oracle evidence are saved.

The oracle closure is supplied to `create_server(... supervised_win32_task_oracle=...)`. It consumes only the final action identity plus independently retained before/after public PNGs; it verifies action `completed`, `release_confirmed`, exact call/operation/generation match, and strict pixel threshold. It returns a receipt bound to those IDs and its unique oracle ID. Retain raw requests/results, PNGs, oracle input/output, timestamps, process custody, exit evidence, and a SHA-256 manifest. This is an integration exercise, not a reliability or efficiency comparison.
