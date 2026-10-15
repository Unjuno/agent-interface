# Cancellation wake pipe saturation: first native A01

**PASS_SCOPED_WAKE_PIPE_SATURATION.** A separate control pipe still needs an admission policy when full. In this fresh18-cell Linux study, blocking one-byte cancellation arrived after all4096 older hint bytes were read; dropping nonblocking EAGAIN lost cancellation in3/3 full cells; publishing a retained current-owner Event first let3/3 full cells close their owned dummy target descriptors with4096 wake bytes still pending and no wake reads. Healthy9/9 cells canceled once. This supports the scoped transport comparison, not production adoption or physical input release.

| Policy | Initial load | Cancel / first cells | N/C bytes read per cell | Wake bytes at primary boundary | Primary targets | Consumer boundary ms: median [min,max] |
|---|---|---:|---|---:|---|---|
| blocking_byte | empty | 3/3 | 0/1 | 0 | both EBADF | 0.230 [0.223,0.286] |
| blocking_byte | full | 3/3 | 4096/1 | 0 | both EBADF | 123.111 [119.162,124.151] |
| nonblocking_drop | empty | 3/3 | 0/1 | 0 | both EBADF | 0.230 [0.195,0.456] |
| nonblocking_drop | full | 0/3 | 4096/0 | 0 | both OPEN | 500.354 [500.262,500.490] |
| level_flag_nonblocking | empty | 3/3 | 0/0 | 1 | both EBADF | 0.362 [0.169,0.400] |
| level_flag_nonblocking | full | 3/3 | 0/0 | 4096 | both EBADF | 0.345 [0.327,0.414] |

All9 full cells qualified capacity4096, initial FIONREAD4096 and native Q-probe EAGAIN11 before consumer drain. Blocking full senders remained pending at the25ms preconsumer checkpoint, then wrote exactly1C; caller write interval median151.917ms [148.589,157.676]. These intervals include scheduling and postreturn observer work. Optional wchan is descriptive; no unobserved kernel entry or syscall residence interval is inferred. Nonblocking full senders returned EAGAIN before consumers began. The retained Event was published before the attempted wake and tested before reads. Healthy level cells intentionally leave their redundant1C unread; scoped cancellation and FD semantics agree, byte traces differ.

The naive full cells remained uncancelled with both original target identities OPEN at the>=500ms primary cutoff. Only the later labelled fixture phase closed them. All72 owned FD lifetimes ended with EBADF witnesses; all36 sender/consumer threads joined. Byte conservation, exact N-before-C order, original FD/dev/inode/mode/flags, checkpoint projections, native PID/TIDs and monotonic event ordering are preserved in [FIRST](results/native/FIRST.json) and18 exact per-cell copies. No failed row or missing cell was discarded.

| Field | Japanese meaning / definition | SI relation / type / scope |
|---|---|---|
| N_read / C_read | 非取消ヒントN / 現在の取消Cを読んだバイト数 | byte counts; nonnegative integers, N<=4096/C<=1 in these cells |
| wake_unread_primary | 主判定時の通知pipe残バイト数 | byte count; integer0..4096 here |
| consumer_boundary_ms | reader開始から取消完了、または主期限観測までの経過 | milliseconds=0.001seconds; derived nonnegative float |
| caller_write_ms | write直前からユーザー空間のreturn観測まで | milliseconds=0.001seconds; includes wait/scheduling; not kernel-only duration |
| n | 各policy/load条件の最初の試行数 | dimensionless integer3; total18, no reruns |

One collector exited0: containerc0975b05…, native PID7, UTC12:01:47.179080–12:01:49.757516, actual host invoking PID44706. One separate pre-frozen saved-only auditor exited0 at12:03:30 with [AUDIT](results/AUDIT.json), checking all18 first observations. Its actual host invoking PID45392, containerc6771360…, source hash, command, start/end UTC and exit are retained. **Auditor native PID and monotonic timestamps were not recorded**; none are invented. The saved-only audit checks evidence consistency, not independent original execution authentication or a committee vote. Raw SHA2561d69a35be425e7f996c3f5a0ab6e8aaad3d242410c0fd40c45741c4d7a02e9f8 remained exact after the audit.

The prospective source commit3bccdf99f657cc6f7426090a202fd59bee494e67 retains all actual parentmain effc43f8… entries and nine inert additions. FREEZE1548310a… and all source/dependency/image bytes were fixed/read back before measurement. Public [freeze5968938700](https://github.com/Unjuno/agent-interface/issues/17#issuecomment-5968938700) mistyped one driver hash; [premeasurement correction5968957571](https://github.com/Unjuno/agent-interface/issues/17#issuecomment-5968957571) gives the correct0d9cb562… string. Actual FREEZE, transferred source and oracle were always unchanged. Original post and correction are preserved, not overwritten.

Pre-freeze construction used synthetic saved JSON: final54 families, each normal/-O108 invocations, three positive families/one HOLD/50 STOP. First macOS errno35 versus Linux11 portability failure and subsequent ordinary v2/v3/v4 repairs remain in the construction archive; they are not native cells or extra formal audits. [CONSTRUCTION](CONSTRUCTION.md) explains the separation. Public historical paths are declared display projections with original/public byte/hash maps; private originals remain retained locally. Projection does not authenticate inaccessible private execution paths. Current portable v4 sources and the first native source/raw/audit are exact, unprojected bytes.

Hardware/backend: observed physical macOS64GiB/10 logical CPUs, shared with other guest owners; owned private OrbStack guest, Linux7.0.5/aarch64/Python3.12.15, cached immutable image in FREEZE. Actual cgroups CPU25000/100000, RAM134217728, swap0, PIDs32; no network, read-only root/source. Native monotonic_ns within each guest process; host/guest monotonic domains are not compared. Balanced fixed order, three repeats per arm; no confidence interval, scheduler pinning, frequency control or clock-resolution/error estimate. Logged observations and quota contribute to durations; no general latency/speed/resource advantage is claimed.

Both finished own containers were removed only after logs/raw/audit/inspect readbacks; private running inventory empty, own job marker released, exact owned VM stopped and read back. [Resource release](results/RESOURCE_RELEASE.json) and operational receipts distinguish observed effects from requests. Source/output directories stay retained in the stopped guest. No foreign VM/default Engine, GPU, model, personal display or task input was operated.

Decision: retain this finite native counterexample and established single-owner retained-state comparator as inert research evidence. Do not promote blocking wake writes or EAGAIN-dropping cancellation. This does not certify any current controller uses either baseline. Event locking under contention, stale generation/ABA, multi-owner cancellation, real backend release, useful feedback, task effect, integrated matched efficiency and full#17/#59 remain unresolved. [Linux pipe semantics](https://www.man7.org/linux/man-pages/man7/pipe.7.html) and [Python Event](https://docs.python.org/3/library/threading.html#event-objects) describe the underlying established primitives; they do not supply application-level authority or deadline guarantees.
