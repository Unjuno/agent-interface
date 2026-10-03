# C05 finite private X11 GIL comparison

C05 is a new readiness/ARM exposure protocol, not a replay of consumed C04. C04 STOP remains. C01 HOLD and C02 dummy-FD finite PASS remain unchanged. Before any positive input, all roles report READY, acknowledge ARM, and the parent observes the complete keymap neutral. Preparation uses20s; cancellation/result gates remain2s. No child spawn after ARM.

First6 cells completed once, fixed saved-only oracle PASS_FINITE_X11_GIL_BOUNDARY and7copied falsifications rejected. Raw SHA256 e1cf715e69f3fb119ddad8f3c58f9fa6e5981e58306d4cce727695cd2fd139e3.

| Case | Mode | Cancel-send-after to first neutral observation (ms) | Contrast |
|---|---|---:|---|
| 0 | thread_cdll | 2.989600 | True |
| 1 | thread_pydll | 252.422171 | True |
| 2 | process_pydll | 4.041522 | True |
| 3 | process_pydll | 0.478170 | True |
| 4 | thread_pydll | 243.836749 | True |
| 5 | thread_cdll | 12.641278 | True |

This metric ends at the first complete parent keymap query showing only the owned key released; it is not adapter release latency, a performance guarantee, or a statistical reliability estimate. Two observations per mode; nominal cancel delay50ms, actual cancellation wholly inside internal300ms native bounds in all6. Shift_L50 owned, F9 75 bystander remains pressed until marked fixture cleanup. Every final complete32byte keymap neutral; children join/exit0/retired; Xvfb exit0; container exit0/OOMfalse. Config Linuxarm64 CPython3.12.15 glibc2.41 privateXvfb2:21.1.16-1.3+deb13u4; image f9b71334; CPU0.25/memory128MiB/swap0/pids32/networknone. These are configuration observations, not total host bounds.

PyDLL intentionally retains GIL; CDLL releases it. Independent process and released-GIL thread neutral observations finish before native end; retained-GIL safety thread release begins after native end. This demonstrates this finite virtual-key fixture only. No physical device/application/model benefit, production backend stall, process-death cleanup, queued-positive fencing, hard deadline, reliability or runtime adoption claim. No formal repeats, peer producer replays, source-ref or main writes.

Prospective public freeze5971474616 preceded first input; producer88702 UTC17:09:19.486372–17:09:46.394613 exit0. Frozen saved-only oracle88816 UTC17:09:57.128310–17:09:57.174298 exit0. OwnVM stopped after0active containers and cold readback. PR7109 delivery of appended inert C05 evidence pending; new content descriptor/reviews and later current-tree/live sender checks required.
