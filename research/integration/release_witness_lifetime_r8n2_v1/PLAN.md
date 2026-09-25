# #4345: recipient lifetime and independent release evidence

Allocation `release-witness-lifetime-4345-20260925-r8n2-01`.
Intake main `9bc9343564a1522df2cf62f4c5cfcdb38194b7c4`.
Parent #3066 / retained PR #4250 STOP/HOLD remains unchanged. This is a new measurement-lifetime question, not a retry of its 14-case fault matrix.

## H / T / D / C / U

H: destroying a recipient removes recipient-local release evidence without determining the X server's key state. A separately connected observer can distinguish a witnessed down-to-up transition, input still held at measurement, and missing observation. No observation grants input authority or task success.

T: 4 scenarios x2 configurations x2 repetitions =16 fresh sessions. Fixed order is repetition 0 then1; within each, bare Xvfb then Xvfb+Openbox; within each, LIVE_RELEASE, DESTROY_RELEASE, DESTROY_HELD, DESTROY_WITNESS_LOST. One case per launcher/tool invocation. Each owns a fresh authenticated TCP-disabled Xvfb, cooperative Xlib recipient, independent read-only F8 witness and non-actuating policy process. Use the complete unmodified X11Backend module and complete contract dependency from the pinned main; call actual focus/key_state/release_all. This does not exercise the full public API/session/CLI or an independently enforcing lease. F8 auto-repeat is disabled in the private server. One task press, no re-press; no other client emits task input.

The recipient window (not its reporting process) is destroyed after the witnessed press in three scenarios. The process remains only to retain old event records and termination evidence. DESTROY_HELD deliberately withholds release until after policy/measurement; this is a negative diagnostic, not an accepted controller. DESTROY_WITNESS_LOST closes the actual witness connection/process before release/post-read; an audit-only separate connection never rescues policy input. Two observation policies classify identical underlying sessions:32 classifications are not32 independent trials.

D: require16 complete first cases; APP_ONLY release evidence4 /UNKNOWN12; SERVER_WITNESS release8 /STILL_DOWN4 /UNKNOWN4. Every press must be independently observed down; destroy must precede release where applicable; held control must be down before cleanup and all terminal input must be neutral after cleanup. All child and launcher exits must be observed0, no source/lineage/order/count contradiction, separate raw-only audit errors0, and12/12 effective copied-evidence controls must reject. PASS_RELEASE_WITNESS_LIFETIME_SCOPED is a measurement result, not a safety PASS of the held-input comparator. Complete scientific contradiction is FAIL; missing integrity/denominator/process evidence is HOLD/STOP. No retries, replacement, exclusion, pooling or post-result threshold/source tuning. Any incomplete launcher stops the remaining sequence.

C: cooperative private X server, one actuator, one incarnation, no re-press, stable keymap and no competing key source. Poll results are not complete event history. Target loss can change routing; key state and recipient consumption are different observables. X-server logical state is not physical HID. A real app with its own global input observer may not lose evidence like this recipient.

U: no complete dependency graph, other faults, backend restart/stall deadline, source authentication, multi-owner input, hard real-time, model/task/latency/token benefit, population reliability, arbitrary GUI/backend or production promotion. Scope-compatible next integration decision: preserve server-neutrality and recipient-consumption evidence separately, returning UNKNOWN when the relevant witness is unavailable. Parent #3066 and global ROADMAP remain open.

## Source and execution conditions

UPSTREAM.json binds exact source bytes/Git objects. ENVIRONMENT.json records this supplied Linux container and installed software; Docker/OrbStack image identity is unavailable. No install/model/provider/user desktop/user documents/experimental external network. All private cookies are ephemeral and removed, not retained. Construction and its failures are separate from formal evidence. The final source freeze includes the launcher, auditor, controls and tests.

Construction incidents: c00 authentication failed before task input because installed Python-Xlib did not match wildcard Xauthority; c05 Openbox target was not yet viewable during initial focus, before task input. Repairs added exact local-family auth after display allocation and a bounded viewable/managed-window readiness predicate. The original c00/c05 source and raw failures remain. Other construction cases are excluded plumbing/observation checks, not formal repetitions. The extra final audit launcher-receipt check is preformal and changes no scientific classifier.

Roadmap: current/ownership intake -> excluded construction -> source/environment/gate freeze and exact Git readback ->16 bounded first cases -> raw audit/controls/tests -> lossless evidence PR -> exact-head checks/scoped review -> qualified merge/readback. Retain branches while any open PR/evidence dependency needs them; do not move refs to simulate deletion.

## Conditional interval proof and variable table

| Symbol | Meaning (日本語) | SI unit | Definition | Domain / assumption | Type |
|---|---|---|---|---|---|
| a,b | 押下状態を返した照会の開始・終了時刻 | s (stored integer ns) | monotonic endpoints of the down query | 0<a<=b | real scalars / integer representation |
| c,d | 解放状態を返した照会の開始・終了時刻 | s (stored integer ns) | monotonic endpoints of the later up query | b<c<=d | real scalars / integer representation |
| s1,s2 | サーバーが各状態を評価した未知時刻 | s | times inside the respective query intervals | a<=s1<=b; c<=s2<=d | real scalars |
| r | その間に生じた唯一の論理解放時刻 | s | down-to-up transition | one actuator, no re-press | real scalar |
| w | 保守的な解放時刻区間の幅 | s | d-a | nonnegative | real scalar |
| N | 独立した私有表示セッション数 | 1 |4 scenarios x2 configurations x2 repetitions |16 planned, no replacement | integer scalar |

Assuming the server evaluates the two successful state queries during their recorded call intervals, it was down at s1 and up at s2. Under one-actuator/no-re-press chronology the transition therefore obeys s1<r<=s2. Combining a<=s1 and s2<=d yields a<r<=d. The implementation reports the conservative closed interval [a,d]. It must not report d as the exact occurrence time, nor use [b,c], which is generally too narrow because the evaluations may occur anywhere inside their respective calls.

Dimension check: all interval endpoints denote the same host monotonic time domain. Their difference w=d-a has units seconds; raw nanoseconds convert by division by 1,000,000,000. X-server event milliseconds are retained as diagnostic fields and are not subtracted from host monotonic timestamps. Example: a=1.000s,b=1.001s,c=1.004s,d=1.005s implies only r in (1.000s,1.005s], width0.005s, not an exact release at1.005s. Missing post-query yields no interval. A post-query returning down supports STILL_DOWN at its sample, not continuous holding throughout all earlier time.

## Primary API background

X.Org Xlib manual, XQueryKeymap: returns logical keyboard state, which may lag physical state when processing is frozen. https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html . This API definition supports observation semantics, not the empirical result or a real-time guarantee.
