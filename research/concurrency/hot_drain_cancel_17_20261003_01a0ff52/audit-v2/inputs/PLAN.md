# Late cancellation during a hot data drain — #17

Worker: 01a0ff52-70ab-7f10-82b3-e60375a032fb; FINAL-v5.
Allocation: 17-HOT-DRAIN-ORBSTACK-A01-20261003-01a0ff52-70ab.
Parent claim: https://github.com/Unjuno/agent-interface/issues/17#issuecomment-5966982679

H: control-first selection at each poll does not alone bound data service after cancellation arrives inside a continuously replenished drain. Existing bounded per-poll read service is the strongest simple comparator. All policies prioritize a returned control key; compare drain-to-EAGAIN, budget1, budget4. No new production mechanism is proposed.

T: enumerate a finite abstract model first. Then one new Linux/OrbStack native-pipe producer and one separate raw-only auditor, retry0. Exactly15 cells: three policies times hot cancel after data read1/read5, prequeued co-ready control/data, cold4-byte data with cancel after read1, cold4-byte data-only. Hot refill writes one D after each D read; cancellation writes C after the selected read and before refill. This directed same-process injection makes actual kernel data availability reproducible without a scheduling distribution. It is not a concurrent producer benchmark. Data/control FDs are separate nonblocking pipes, with both writers retained through the primary phase. Max16 primary reads and32 polls per row; first unexpected failure stops the producer. Limits are diagnostic stops, not successful cancellation.

D fixed before results: retain a scoped discriminator only if all15 rows and source/environment pins, typed FD/inode identities, exact byte ledger, poll→read binding, refill/cancel cause, primary/cleanup separation and five actual FD-close checks agree with independent reconstruction. Hot drain must reach16-read CUTOFF with pending C collected only in cleanup. Budget1 must ACK at read1/read5; budget4 at read4/read8. Co-ready ACK at zero D reads for all; cold late ACK at1/4/4 respectively; data-only consumes exactly4 D with no C. These are authored directed conditions, not frequencies. Any identity/order/denominator mismatch: HOLD/STOP, retain first result, no formal retry. Scientific rejection of the unbounded drain is distinct from producer/auditor exit success.

C/U: refill and cancel are programmed in the same process; CPU scheduling, independent log/journal stalls, blocking arbitrary callbacks, continuous races, natural loads, OS portability and wall-time cancellation bounds remain unknown. Event timestamps are provenance, not latency statistics. Bound concerns additional read operations when control is already pending, not seconds. A separate blocking callback or inaccessible control FD can violate other contracts. No GUI/model/input authority, task effect or physical key release is exercised. This is a refinement of the late-arrival gap expressly excluded by #6927, not a replay of its co-ready allocation or #6915/#6942/#6896.

| Symbol | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| k | pollごとのdata読取り上限 | 1 | 1または4、比較対象はEAGAINまで | 整数 |
| r | cancelを書込む直前までのdata読取り数 | 1 | 実測1または5、列挙1..15 | 整数 |
| n | primaryの累計data読取り数 | 1 | 0..16、各readは1 byte | 整数 |
| t | monotonic_nsから保存するイベント時刻 | ns | 同一process時計、硬いdeadlineの根拠にしない | 整数 |

Resources: only existing owned guest research-6501-async-01a0ff52-70ab and retained python image sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016. One container, network none, root/source read-only,0.25CPU/128MiB/32PIDs, output<2MiB, outer30s. No pull/default/shared daemon, GUI/GPU/model/input. Freeze all source/input/environment/runner/auditor hashes and exact commit before formal start. Construction receipts are excluded from formal counts. Stop the owned guest after preserving output and checking container exit; retain source/image/first failures.

Analytical basis and primary sources: Python selectors documents readiness and select(0), https://docs.python.org/3/library/selectors.html (PSF documentation; accessed2026-10-03); Linux epoll(7) starvation discussion describes readiness-list round-robin, https://man7.org/linux/man-pages/man7/epoll.7.html (Linux man-pages; accessed2026-10-03). The explicit future-control directed contrast is our inference, not a claim that documentation measured these cells. No external source code is copied.
