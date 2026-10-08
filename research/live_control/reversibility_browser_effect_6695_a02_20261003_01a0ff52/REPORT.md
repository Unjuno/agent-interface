# #6695 A02: conditional frontier in a real headless form

`PASS_METHOD_SCOPED` and `H_PASS_SCOPED` for the fixed16-context fixture gate. One candidate launcher and one separate raw-only auditor exited0, retries0. All16 controller/server/effect records reconstruct with errors[]. A01/#6872 and T0/#6707 remain unchanged. This is native browser/HTTP application-session evidence; authored delays and deterministic known selectors are not a natural latency or model/general GUI benchmark.

| Policy (8 authored cases) | Correct commits | Wrong commits | Deadline refusals |
|---|---:|---:|---:|
| STAGE | 6 | 1 | 1 |
| WAIT | 3 | 1 | 4 |

The cheap B case c00 had preparation400ms, signal300ms, edit0ms, effect deadline600ms. STAGE actually committed correctly at524.025ms; WAIT arrived at771.004ms and the server refused with no effect. In expensive B c01 (edit800ms, deadline1000ms), STAGE arrived at1337.746ms and was refused; WAIT committed correctly at756.552ms. These are first observed single-fixture witnesses, not repeated performance measurements or estimates of production rates. Measured preparation intervals for these arms were401.865–405.107ms; the expensive staged edit was805.087ms. Selector/HTTP/scheduler overhead remains in the actual event times. Alternating order controls only the authored schedule; host load is unrandomized and uncontrolled.

UNKNOWN with hidden truthB committed A incorrectly in both policies. The server deadline guard prevents a late fixture effect; it cannot make uninformative decisions correct. Do not promote staging as universal optimization or safety, and do not substitute the requested service delays for observed application timing.

## Independent evidence and interpretation

The controller reads the visible signal/ready status and changes the actual DOM form through Playwright. It receives only trial IDs/policies, not future fixtures or scorer truth. Its process did not read the server effect ledger. The server knows the authored signal/service/deadline fixture but never loads truth.json. It changes a reversible draft until commit. Check and effect append occur under one per-trial lock; the timestamp is that admitted application-session boundary. A separate stdlib auditor imports neither controller nor application and reconciles actual server events/effects, controller status, complete roster, observed interval bounds and scorer truth. No post-result thresholds or formal source changes occurred.

The fixture ledger is in memory, with no undo endpoint, and is serialized after the run. This is a concrete effect in the disposable app session; it is not durable filesystem commit or an external user application effect. Server clock values are relative to its own monotonic origin. Browser/process timing is not mixed with that clock. Information delivery is logged when the server first responds after eligibility; timing precision does not prove cross-device clock comparability.

[Protocol](PROTOCOL.md), [source/runtime freeze](FREEZE.json), [source/execution binding](SOURCE_EXECUTION_BINDING.json), [raw server ledger](formal_01/server.jsonl), [controller raw](formal_01/controller.jsonl), [audit](AUDIT.json), [execution receipt](formal_01/EXECUTION.json), [manifest](SHA256SUMS). Frozen README describes the prospective source phase; this report and execution binding give the completed disposition.

Original construction failures and three distinct mini invocations remain under construction/. The final private mini validates the explicitly selected Chrome executable, and all10 unit tests pass, including7 actual evidence corruptions, effect-before-commit absence, single admission, equality and +1ns refusal, hidden future signal, rejected edit preservation and complete HOLD schema. Construction cases are not pooled with formal trials.

Native macOS arm64 Python/Nodev24.19.0, Playwright1.62.1, explicitly selected Chrome for Testing151.0.7922.34. Freeze pins the controller/application/auditor and ten source/input/protocol files plus Node, package manifest, Chrome executable and main framework. It does not hash every OS/transitive binary/resource. Single fresh browser context per trial, headless with GPU/background-network flags disabled. Context interception admitted only the private loopback origin; formal blocked external page requests0. This is not an OS network namespace or hostile-code secrecy boundary, and no enforceable CPU/RAM cap is claimed. No user browser/profile/display, model, OS pointer/keyboard, shared VM/Docker or production runtime was used. All contexts and the owned browser closed normally; server stopped. The child ran02:01:26.593–02:01:58.411 UTC (includes startup/context overhead; not task latency).

Audit argv/exit0/stdout/stderr were observed, but audit start/end wall timestamps were not instrumented. Its binding receipt was created after observing the result, explicitly not backdated or claimed to be a prospective freeze. File creation time is not the command start. The candidate receipt contains actual start/end observations and finite output9598 bytes; raw serialization hashes remain independently checkable.

Server raw SHA-256 `54973b09164825ee72bbe7f40dbdcbf43514b9e4588f9fe7dcec6449ace74192`. Source commit `564530981e6cf834c3d6ac607a94734afacba10b`; later metadata-only whitespace preservation does not change any frozen file. Original unittest progress-line trailing space is preserved by one file-specific attribute. Main not updated; FINAL-v5 content consensus/current-base nonauthor combination confirmation still required. No hosted CI completion is claimed.

Disposition: retain observed reversal and UNKNOWN failure, use a matched simple wait comparator when evaluating real application staging. Any next real website/model/physical-input allocation needs separately admitted resources and measured application-specific reversibility/effect/cost bounds; this fixture alone does not complete #6695 or the full computer-control goal.
