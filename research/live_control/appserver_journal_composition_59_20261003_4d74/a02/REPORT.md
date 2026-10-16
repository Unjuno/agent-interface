# A02: request-journal deadline composition

**PASS_SCOPED_COUNTEREXAMPLE** in one six-cell Linux allocation. Frozen source: bf571f165fd9b96532e6a2acbe383d469d496120; PR #7001. A01 remains an immutable setup STOP in merged PR #6994. Its data and counters are not pooled with A02.

| Cell | Caller event window (ms) | Peer received bytes | Journal rows |
| --- | ---: | ---: | ---: |
| main healthy | 4.013083 | 70 | 2 |
| main held | 404.901613 | 70 | 2 |
| composed healthy | 3.891067 | 70 | 2 |
| composed held | 401.287938 | 0 | 1 |
| bounded healthy | 4.762381 | 70 | 2 |
| bounded held | 50.472099 | 0 | 0 |

The three healthy arms returned the exact echo. With the mutex held, main and the fixed send/close composition were still pending at the checkpoint. Main later returned an exact echo; the composed arm later raised its pre-send budget TimeoutError. Bounding sent-journal mutex acquisition returned the distinct journal-lock TimeoutError before the checkpoint while the holder remained active.

The checkpoint was scheduled for 250 ms and occurred at 252.847–260.803 ms. Release was scheduled no earlier than 400 ms and began at 400.100–400.235 ms. Setup readiness preceded every call, within the new two-second gate. Scientific 50/250/400 ms settings and all client bytes were unchanged from A01.

## Execution and evidence

Construction ran once and passed (10:03:03–04 UTC). Producer ran once and exited zero (10:03:15–24 UTC). The saved-output auditor ran once and exited zero (10:03:34–36 UTC), reconstructing all six cells and rejecting five copied corruptions: timestamp, peer byte, outcome, duplicate cell and cleanup. Retries: zero.

The auditor author is distinct from the producer/client author. A direct saved-data review by that auditor author is independent of the producer, but is not a non-author review of the auditor implementation. A separate non-author content review is recorded separately. Corruption controls validate these five evidence checks; they do not prove general implementation correctness or product benefit.

All six worker and peer processes were reaped; all caller, holder and reader threads retired; all three pipe wrappers and journals closed without cleanup or thread errors. Every peer exited zero through normal EOF. The driver closed stdin and reaped peers before client.close, so these endpoints do not validate close-alone retirement under contention.

All 54 actual artifact hashes and 15 frozen source/document hashes match. Raw source hashes before and after match the fixture. Candidate and auditor mounts were separated and read-only. The cached Linux/amd64 Python 3.12.14 image used WSLc with network none, pull never, requested 0.25 CPU and 512 MiB. The swap-limit/cgroup warning is retained; requested configuration is not proof of enforced isolation.

## Supported conclusion and limits

The pinned send/close composition leaves a request-side sent-journal mutex wait outside its caller deadline in this fixture. The reference change bounds that acquisition. This respects the original authors' journal-I/O exclusions; it does not disprove a broader guarantee that they did not claim.

The 50.472099 ms is a driver caller-event window, not a strict 50 ms method guarantee. Journal observed_ns precedes lock acquisition and does not timestamp file-write completion. A sent row is intent before pipe writing and proves neither send nor no-send by itself. Zero peer bytes measures no child receipt; absence of OS-write entry is separately inferred from the exact source/error branch, with no syscall-entry instrumentation.

File write/flush, serialization, other locks and predicates, Windows, partial writes, notify, model/game/GUI/input, physical release, independently useful feedback, token efficiency and the #59/#57/roadmap gates remain untested.

## Version boundary and next integration decision

The tested close proposal is fixed V1 #6955 at 31f10e660d2e7e13d8fe05c9a56d3f3c5e71f324, blob b1d4762ae4d3ccef8c4dd73198c01b247a2c07e7. After A02 finished, its owner advanced V2 to dd322c2d355a4ab4d917d3216a5fe08ab8b83eff, adding reader.is_alive refusal before journal closure. A02 did not execute or qualify V2. No consumed allocation is refrozen or rerun.

Hand this scoped sent-journal deadline change and its immutable evidence to the existing #6965 send owner. Preserve V2's reader guard, current main's no-drain EOF, #6991's UTF-8 scope and other source owners. Apply scoped deltas onto fresh main; both older full donor snapshots contain the obsolete stderr.read EOF path. Public adoption still needs the owners' exact integration and platform qualification. This PR adds evidence only.

README and SOURCE_SHA256SUMS record the immutable source-freeze state. REPORT and RESULT describe actual execution.
