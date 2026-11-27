# R20 result — terminal UNKNOWN during a held Win32 callback

R20 ran once on 2026-10-23 against source `18541e1752cc26dcae45591a50f81697dbf853dd` on the user-authorized Windows PC. The input-free preflight passed. One public stdio-MCP dispatch and one cancel targeted a fresh owned fixture; the exact R20 sentinel was clicked, entered, and saved. The cancel response took 1.463 ms and returned `pending`.

The exact producer (PID 39056, creation time 134372646025352181) was observed exited at +240.479 ms, while the callback remained held. Cancellation and action both reached `unknown` at +2874.578 ms, before the 4011.304 ms hold ended. During that window, release and replay remained false and `task_success` stayed null. `interface_close` remained `busy` with cleanup `UNKNOWN`. The held injected Q-down was suppressed when the callback returned. The exact fixture effect, fixture exit, hook thread exit, and restoration of the previous foreground window were observed.

An independent same-generation child readback completed at +194.855 ms with `q_down=false` while the injected Q-down callback was still held; its callback returned at +4013.465 ms. The callback waits before forwarding the event, so this UP sample reflects a not-yet-delivered event and cannot prove release.

The frozen audit remains **FAIL_OR_UNKNOWN (7/10)** and is preserved unchanged. Three checks read callback-return/suppression fields from the pre-release hook snapshot. The independent supplemental audit reads the retained post-release event rows and the held-window readback and passes **4/4**, supporting the intended bounded terminal-UNKNOWN and readback-ambiguity questions for this one run. This result does not establish input release while the callback is blocked, successful recovery, MAP01, WSLc portability, efficiency, or broad reliability. The final Q-up sample occurred after the Q-down was suppressed and cannot be counted as proof that an input was released. No retry was made.

Raw output, preflight, frozen conditions and audits are retained in this directory.

`SHA256SUMS.final` hashes UTF-8 text after normalizing CRLF to LF; it hashes the PNG by its exact bytes. The pre-run freeze manifest retains the original frozen-input hashes and was verified allowing the Windows checkout's CRLF conversion.
