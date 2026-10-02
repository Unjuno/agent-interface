# Same-connection focus reply and key-state acquisition — q4s8

Issue #4389. Intake main 4c701cc51b06296268ad8d9ae3eff1dd6f2d379d.
Owned branch research/key-state-piggyback-20260926-q4s8; new path research/measurement/key_state_piggyback_q4s8_v1/ only.
No shared runtime, root files, workflows or historical data change.

## Purpose / preservation

The prior n6k4 experiment remains HOLD_NO_20_PERCENT_FULL_ACQUISITION_GAIN, with 40 blocks,2800 acquisitions and no request reduction. Its unchanged 268-file ZIP is conversation-hosted; its hash and successful raw-only reconstruction are retained here, not a claim of full remote publication. Prior focus/keymap PR4123 is already merged and is not rerun. This allocation tests composition with a required focus reply, NOT a rerun or a replacement of those measurements.

## H

H1: a SAME subscribed connection's XGetInputFocus reply, after the writer has acknowledged completion, makes preceding selected events available for local queue draining. FOCUS_PIGGYBACK can report the same Shift state and focus as FOCUS_QUERY and FOCUS_SYNC with one rather than two requests per bundle.
H2: an OTHER connection's reply does not populate that observer's Xlib queue. Its zero-I/O local read can remain stale. A subsequently declared sync on the observer recovers the selected events; this is a diagnostic, not hidden retry of a formal case.
H3: complete focus-plus-state time is at least20% lower for piggyback than focus plus direct query, overall and in every context. H3 can fail independently of H1/H2. No request-count inference substitutes for measured cost.

## T / minimum denominator / process boundaries

Provided Linux x86_64, CPython3.13.5, installed gcc/libX11/Python-Xlib0.15/Xvfb. Docker/gh absent; no Docker/OrbStack image-attestation claim. Private authenticated TCP-disabled Xvfb, ordinary XTEST Shift changes confined to owned windows. No model/provider, user desktop/documents, installations or experimental network. No text task or public runtime/CLI is executed.

Four contexts UP, DOWN, EDGE_BURST (eight down/up pairs then down), FOCUS_RETURN (away,down,back). Three fresh window/four-observer blocks per context:12 matched blocks. Writer/witness/server persist only inside each context. Four immutable serial context batches in that order; each once. An incomplete/nonzero batch stops allocation; no further batch, retry,replacement,exclusion,pooling or postfreeze tuning.

Three primary reader connections, all with identical event subscriptions and detectable autorepeat setup. Each bundle genuinely returns focus and Shift: FOCUS_QUERY = XGetInputFocus plus XQueryKeymap; FOCUS_SYNC = XGetInputFocus plus XSync and event drain; FOCUS_PIGGYBACK = XGetInputFocus plus QueuedAlready drain. The added C focus entry point uses the SAME Ctx/display as the following observe call; request serial continuity is independently checked. Both event modes invoke the unchanged prior Python reducer over retained per-block history. This is not an incremental-reducer optimization. Additional fourth connection is only the OTHER_CONNECTION_REPLY/local-only/sync diagnostic. The other reply is executed on primary QUERY's connection, so its request is outside primary timing and fully retained.

Per block17 triples in rotated arm order: sample0 first exposure,1-2 excluded warmup,3-16 fourteen primary triples.612 acquisitions total,504 primary,36 first,72 warmup;12 local-only and12 diagnostic sync observations separate. No first exposure is called warm. Timed bundle includes Python focus conversion, ctypes/native acquisition, prior adapter receipt construction and state reduction; it excludes outer result construction, JSON output, setup,writer/witness and teardown. Full wall/CPU, nested native brackets, event bytes and exact request/processed serials are retained. Full-time ratios use each block's median per arm; samples within a block are technical repeats, not independent machines.

Actor command/reply stdout text and exact stdin text, application-independent witness keymaps/focus/buttons, process identities/argv/exits, Xvfb teardown and all source/environment hashes are retained. Initial and terminal full keymaps must be zero; endpoint equality is supported by the declared single quiescent writer, not a proof of arbitrary history. XQueryKeymap is server-logical state, not physical HID. Candidate packets do not receive witness data or scenario labels. Actor alone receives the frozen context to generate fixture state.

Native code: acquire.c is the exact prior3102-byte native.c prefix plus one focus function. actor.py,server.py,native.py,predecessor_policy.py are exact inherited files, bound in LINEAGE.json. upstream_infra.py is a NEW minimal implementation of only the server helper's now/save/sha utilities, not the old infrastructure module. New run/bundle/execute/audit/controls/test code is research-only. C structures use native ABI; ctypes sizes are checked against exported C sizes before use. No packing override or undocumented layout is assumed.

Outer execute.py creates an exclusive consumed marker and enforces25s runner limit; TERM then5s grace then KILL only of its owned process group. run.py handles TERM with cleanup when Python regains control. Actors have3s response waits. Every batch requires prior actual zero exit. A timeout remains STOP even if later cleanup succeeds. All processes finish in this conversation.

## D

PASS_FOCUS_REPLY_PIGGYBACK_CONTRACT requires12 blocks/612 acquisitions, exact schedule/source/process/neutral cleanup, state/focus equality to the independent witness in all three arms, request counts2/2/1, zero additional requests in piggyback's drain, and separately implemented raw-only audit with10 effective copied-evidence controls. OTHER_CONNECTION_REPLY returns stale UP in all9 non-UP blocks, then explicit observer synchronization recovers; UP positives stay UP. Complete mismatch is FAIL, missing source/process/denominator or ineffective controls is STOP/HOLD.

Separately PASS_FOCUS_STATE_LOCAL_COST requires median of the12 block PIGGYBACK/QUERY full-time ratios<=0.80 AND each context's three-ratio median<=0.80. Otherwise HOLD_NO_20_PERCENT_BUNDLE_GAIN. All block medians and ranges, first exposure and native/full endpoints remain visible. No calibrated physical uncertainty or confidence interval from three blocks per context is manufactured.

## C / U

Required focus observation is part of this newly authored bundle; callers not requiring it obtain no free synchronization. Same-connection reply processing is conditional on selected events already generated, no loss and the quiescent source interval. Neither a response, byte hash nor reconstructed state establishes future input authority, event-history completeness under arbitrary grabs/reconnect, physical state, application completion or atomic check/use. QueuedAlready-only on another connection is deliberately NON-equivalent and is not included as a valid speed competitor.

Guest CPU0 affinity for runner/server/actors; no frequency lock or physical exclusivity. Python allocation, syscall scheduling, native clock sampling and history replay contribute costs. Retained raw clocks support descriptive results only. No actual model/GUI-task/token gain, natural failure probability, energy, production adoption or global ROADMAP completion. Auditor is separate implementation/process by the same author, not independent human review.

## Variable table

| Symbol / field | 意味（日本語） | SI単位 | 定義 | 定義域・前提 | 型 |
|---|---|---|---|---|---|
| t0,t1 | 区間開始・終了 | s（記録ns） | 同一CLOCK_MONOTONIC標本 | t1>=t0、同一容器時計 | 整数スカラー |
| W | 完全bundle時間 | s | (end_ns-start_ns)*1e-9 | primaryはsample3..16 | 正スカラー |
| c0,c1 | CPU時間標本 | s（記録ns） | process_time_ns | 同一process | 整数スカラー |
| C | bundle CPU時間 | s | (cpu1-cpu0)*1e-9 | C>=0 | スカラー |
| r0,r1 | 次要求番号 | 1 | XNextRequest前後 | 同一接続、今回wrapなし | 整数スカラー |
| R | 発行要求数 | 1 | r1-r0 | focusとstateに別計測 | 非負整数スカラー |
| p0,p1 | 処理済み要求番号の知識 | 1 | XLastKnownRequestProcessed | 全サーバー総順序ではない | 整数スカラー |
| K | キー配列 | 1 | 32バイト、256論理bit | server state、HIDではない | bitベクトル |
| k | Shiftキーコード | 1 | actor readyとsourceに束縛 | 整数8..255、Boolean不可 | 整数スカラー |
| mQ,mP | 対応block中央値 | s | QUERY/PIGGYBACKの14個Wの中央値 | 同一context/block | 正スカラー |
| rho | 対応時間比 | 1 | mP/mQ | 同一blockのみ | 正スカラー |
| u_c | 合成標準不確かさ | s | 校正と誤差モデルが必要 | 今回推定しない | 未取得スカラー |
| coverage factor | 包括係数 | 1 | 校正に基づく係数 | 今回設定しない | 未取得スカラー |

## Conditional derivation / ERROR CHECK

1. The initial independent query supplies a neutral seed; setup drains preceding events. The sole writer then publishes exactly the listed operations and acknowledges its server processing. It performs no mutation during acquisition. This is an explicit experimental ordering condition.
2. The focus request on the SAME reader is issued only after that acknowledgement. Under Xlib's reply/event handling, preceding selected events encountered while obtaining the reply are queued for that Display. The experiment checks this implementation residual with actual native events; no future event or unrelated connection is inferred covered.
3. The prior reducer starts at the exact seed, applies every selected edge in ordinal order, invalidates at focus loss and requires a focus-return KeymapNotify before continuing. Induction over the retained events establishes the last reconstructed Shift bit under those coverage assumptions. The independent checker replays from raw fields rather than trusting status strings. It also compares to a separate actual query before and after acquisition.
4. In the measured functions FOCUS_QUERY issues focus1+query1 requests; FOCUS_SYNC issues focus1+sync1; PIGGYBACK issues focus1+local0. Per-connection measured serial increments must equal2,2,1 respectively. This counts protocol requests, not packets, bytes, model calls or tokens. OTHER_CONNECTION_REPLY cannot transfer one Display's local queue to another; the fourth reader's diagnostic tests that distinction.
5. Convert ns to seconds only within a single monotonic domain. W has time dimension; rho divides seconds by seconds and is dimensionless. Request counts and key bits are dimensionless. No X11 millisecond event time is subtracted from monotonic ns. No count can prove a time speedup; the separate0.80 gate tests it.

## Primary specification / roadmap

X.Org Xlib C Language X Interface: Handling the Output Buffer, Event Queue Management, Key Map State Notification Events, Controlling Input Focus. https://xorg.freedesktop.org/archive/current/doc/libX11/libX11/libX11.html . Documentation motivates the test; local measured outcomes are authoritative at this scope.

Excluded construction and retained correction -> complete public source/gate readback -> four one-shot context batches -> raw-only audit/effective controls -> complete source/raw/result PR -> exact-head applicable checks and scoped review -> qualified research-only main merge/readback. Parent#2107/#57/#2789 and globalROADMAP stay separate.
