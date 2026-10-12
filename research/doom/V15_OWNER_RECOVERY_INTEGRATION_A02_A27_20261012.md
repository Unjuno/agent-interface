# V15 owner crash recovery findings, A02–A24

The V15 process-owner experiments A02–A15 are indexed in their per-allocation folders and PR #8876. They established a real owner-service-death stuck-input case (A14), a guarded but manually driven emergency release primitive (A15), and multiple setup stops. This continuation adds a durable owner-state ledger and supervisor recovery path.

| Allocation | Classification | Result |
|---|---|---|
| A16 | `STOP_CANDIDATE_EVENT_ENVELOPE_MISMATCH` | Independently saw `a`, `d`, Button1 down and owner zombie; ledger preserved all three. Candidate passed `{type,event}` wrappers incorrectly, so recovery was not invoked. Stored raw replayed after parser repair; no retry. |
| A17 | `STOP_CANDIDATE_EVENT_ENVELOPE_MISMATCH` | Same wrapper mismatch remained. No retry. |
| A18 | `FAIL_UNVERIFIED_RELEASE_EVIDENCE` | Recovery was reached, but event/state conjunction did not pass and no failed-attempt details were persisted. Actual final input state is unknown from this allocation. |
| A19 | `FAIL_BUTTON_RELEASE_EVENT_NOT_OBSERVED` | Keys had Release events and verified up; Button1 mask was verified up but ButtonRelease was absent. Added fsynced diagnostic evidence. |
| A20 | `PASS_DIAGNOSTIC_ONLY` | Private Xvfb event-routing probe showed ButtonPress/Release event masks are exclusive per window/client and identified competing event selections as a cause. |
| A21 | `FAIL_BUTTON_RELEASE_EVENT_NOT_OBSERVED` | Removing the candidate's preselected ButtonRelease mask did not suffice while its ButtonPress observer remained the button-event recipient. |
| A22 | `PASS_DIAGNOSTIC_ONLY` | Two client selections for ButtonPress and ButtonRelease coexist, but the press recipient receives the tested event stream under XTest routing. |
| A23 | `STOP_CANDIDATE_REDUNDANT_OBSERVER_DRAIN` | Recovery receipt recorded verified KeyRelease and ButtonRelease and all inputs up. Candidate then tried to read the same observer queue a second time and marked itself false. Preserved as STOP, not scored PASS. |
| A24 | `PASS_METHOD_SCOPED` | With no competing ButtonPressMask observer, post-death supervisor observer released only ledgered keys and Button1; independent events and all-up state were recorded in an fsynced ledger-bound receipt. Session remained alive; Xvfb exited 0. |
| A25 | `PASS_METHOD_SCOPED` | Repeated the A24 recovery path after adding strict same-display/focus validation for injected observers and refusal to overwrite an existing emergency receipt. Frozen hashes matched; two keys and Button1 were independently observed released and up. |
| A26 | `PASS_METHOD_SCOPED` | Exercised `ControllerFailureCleanup.__exit__` with the actual process-owner backend and an owner SIGKILL. The normal receipt gate recognized the ended PID generation and immediately fell back; the outer failure receipt recorded verified emergency recovery and `display_reuse_allowed=true`. `cleanup_complete` correctly remained false because reader retirement, score terminal, and owner-events closure were outside this candidate's evidence. |
| A27 | `PASS_METHOD_SCOPED` | Started the real `InputOwnerProcess`, closed it normally with no inputs admitted, and confirmed the fsynced empty verified-close receipt matched ready PID/start ticks/owner ID and passed the normal outer receipt gate after service exit 0. |

The bounded repair adds a fsynced per-operation intent/ack ledger, process start-tick identity, strict reconstruction of possibly held inputs, focus/surface/geometry and pointer checks, process-death verification, restricted XTEST releases, independent state/event observation, and durable verified or unverified receipts. The outer V39 success and failure-cleanup paths call `verify_or_recover_owner_process`; they first prefer the existing owner close receipt and use emergency recovery only after the owner receipt gate times out.

Local verification: the focused process-owner / cleanup suite passes 14 tests. A24 is one WSL2/Xvfb run with two keys and one button. It does not prove physical-device input attribution, multi-button or mixed-focus recovery, full V39 failure-path integration, game/model feedback, or task-effect correctness. This is not product-level computer-control completion.
