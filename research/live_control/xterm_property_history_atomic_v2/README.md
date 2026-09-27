# XTerm property-history boundary: HOLD and atomic successor

Issues [#3942](https://github.com/Unjuno/agent-interface/issues/3942) and [#3956](https://github.com/Unjuno/agent-interface/issues/3956), 2026-09-22 JST. Intake main: `b2457b746a6df06f6536585dfe2ab937aff639f4`. Research only; no shared runtime, root README, prior result or other worker path changes.

## Results

**#3956: PASS_ATOMIC_TRANSPORT_PROPERTY_BOUNDARY_SCOPED.** One fresh formal orchestration completed 24/24 private Xvfb/XTerm sessions. A separately implemented stdlib auditor, executed in another process, passed with zero errors and rejected 8/8 corrupted-evidence variants. This is not an independent human review.

| Successor measurement | Result |
|---|---:|
| Selected consumer / observer WM_NAME notifications | 48 / 48 |
| Incorrect historical values, EARLY reads | 0 |
| Incorrect historical values, DELAYED A to B | 4 |
| Incorrect historical values, DELAYED A to B to A | 4 |
| Incorrect historical values, DELAYED single A | 0 |
| Separated current snapshots / historical UNKNOWN | 48 / 48 |
| Invented history or authority in separated policy | 0 |

The naive interpretation fails in eight deliberately scheduled cases. The boundary study passes because it observed the preregistered counterexamples and controls. Eight errors are not a natural race-rate estimate. UNKNOWN is not recovered history, and a title is not a general task-completion receipt.

**#3942 remains HOLD_INFRASTRUCTURE.** Its first formal command completed 23 sessions; the last `r3-aba-early` row timed out awaiting the second child acknowledgement. All 24 rows, including that partial row, are retained: 46 consumer events exist, but only 45 belong to the 23 complete rows. The auditor's `totals.sessions=24` counts rows, not completed sessions. Its four errors remain:

```text
runner_error
trailing_event_boundary
malformed_row_23:KeyError:'xterm_exit'
completion
```

XTerm exit 0 did not establish protocol completion; the partial row lacks a verified child terminal receipt. No missing row was replaced, no formal allocation retried and no predecessor observations pooled into #3956.

## H / T / D / C / U

**H:** Reading a current property while draining old PropertyNotify events can falsely assign that value to an earlier event time. Separate the event hint and current snapshot without inventing historical payload.

**T:** Actual XTerm children emitted fixed OSC-2 title sequences A, AB and ABA. Fresh private Xvfb/XTerm sessions used separate observer/consumer connections. The observer confirmed each title before advancing a barrier. EARLY consumed after each transition; DELAYED after the final transition. Four balanced repetitions of six cells made 24 sessions/48 selected events per connection. Both shadow policies used the same consumer stream without observer history. Raw 32-byte events, server times, property bytes, host read brackets, commands, acknowledgements and process/window identities are retained. Other property events are retained with a predeclared WM_NAME selector. No clock conversion or timestamp-as-revision claim is made.

**D:** Freeze required 24 complete sessions/48 events, exact source/environment/schedule binding, complete protocol receipts, EARLY false history 0, DELAYED false history 8, snapshots/history UNKNOWN 48 and eight corruption rejections. #3942 misses completion; #3956 passes. Issue source-hash/command freezes preceded formal execution; full source/archive publication followed it. There was no preformal full-source GitHub readback.

**C:** Barriers select interleavings and perturb timing. This is an adapter-contract study, not an X11 defect. PropertyNotify and GetProperty have distinct contracts. Sources: [X.Org protocol](https://www.x.org/releases/X11R7.7/doc/xproto/x11protocol.html), [XTerm OSC sequences](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html).

**U:** No natural race rate, latency benefit, model utility, token savings, arbitrary application, crash/reconnect/wrap safety or production readiness is established.

## Transport correction and preserved failures

#3942 construction-01 stopped on WM_NAME string/bytes handling; construction-02 retained three cases then stopped on an immediate child-disappearance check; construction-03 passed six cells. All excluded records and source versions matching original run hashes are archived.

Direct command writes followed by child existence/read checks could expose partial JSON. The old transient bytes/exception were not recovered, so historical causation remains unknown. #3956 changed only command publication to a full same-directory temporary file, flush/fsync and atomic replace, adding command/error/terminal journals and their audit checks. A separate-reader construction rejected a held direct-write prefix, saw no final path before replace and a complete value afterward. Six fresh live construction cells passed before freeze. This does not establish arbitrary-filesystem crash durability or authenticity.

## Evidence and offline verification

Seven `retained.json.xz.part00` through `part06` files concatenate to 36,032 bytes. The archive maps 247 paths to exact UTF-8 contents: 138 predecessor and 109 successor files, including all source, freezes, construction failures, formal/partial rows, journals, stdout/stderr and audits. SHA-256:

```text
cecb3b5bc63de93d70502c603bba8d5dc6c07233f080e1bcff3f724d959927d8
```

Returned Git blob IDs matched local objects. `verify_bundle.py` checks the full digest, bounded decompression, paths, file count, frozen sources, audits and raw-file hashes without importing or executing experiments. Extract to a NEW directory:

```sh
python verify_bundle.py --out /tmp/xterm-history-retained
cd /tmp/xterm-history-retained/xterm_property_history_atomic_v2
python audit.py formal-01 --freeze FREEZE.json --controls
```

Successor audit: exit 0/PASS. Same command in `xterm_property_history_boundary_v1`: exit 1/retained FAIL. Reconstructed offline audits matched the original stdout byte-for-byte (`PUBLICATION_CHECK.json`); no live formal rerun occurred. Do not rerun either historical allocation. New live replication requires a new Issue/freeze/output.

Audit SHA-256:

```text
#3942 6318eefab203948f74357479b63e4751b498ae551b88057848ff3ff393ee2935
#3956 ea580e8dd3a0e3c03475e8973f50e13358e374637c05bd91a8c2670c23d8d025
```

Environment: provided Linux 6.18.44 x86_64 container, CPython 3.13.5, XTerm 398, installed Xvfb/python-xlib. Docker absent; not Docker/OrbStack replication. Exact binary identities are frozen. No model/provider, network experiment, installation, game, user desktop, XTEST or keyboard/mouse input.

## Integration handoff / roadmap

Preserve #1764/#1786. #493 was excluded as duplicate; concurrent #3929 and #3924/#3926 scopes were untouched. For #2789/#3876: **a change hint must not mint historical values from a later read**. Keep event provenance/read brackets separate; require producer value/version binding to claim history. **Process exit must not replace a protocol terminal receipt.**

Intake, H/T/D/C/U, construction, freezes, first outcomes, audits, corruption controls and lossless handoff are complete; the PR records repository integration. Production adapter and matched end-to-end validation remain OPEN. This does not close #1786/#2789/#3876 or the repository-wide ROADMAP and promotes no production implementation.
