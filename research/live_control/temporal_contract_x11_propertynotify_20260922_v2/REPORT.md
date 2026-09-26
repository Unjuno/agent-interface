# Live X11 PropertyNotify temporal-monitor transfer — allocation 2026-09-22-002

Issue: #1786. Parent semantic result: #1764 / PR #1783.

Decision: **PASS_TEMPORAL_CONTRACT_X11_PROPERTYNOTIFY_SCOPED**.

## H / T / D / C / U

**H.** Distinct X11 properties encode A, B and heartbeat. Using raw X server PropertyNotify timestamps as the unchanged A3 monitor clock should reproduce the frozen A_THEN_B_WITHIN(80ms) outcomes on a real private X11 event stream.

**T.** Supplied Linux x86_64 execution container; CPython3.13.5, Tk8.6, python-xlib0.15, private Xvfb320x180x24, separate watcher/publisher X connections. No XTEST, keyboard/pointer/task input, model/provider/network/user desktop/shared runtime mutation. After three retained construction STOPs, construction-04 changed only case process isolation and passed 3/3. Source and gates were then committed/read back on GitHub before one formal supervisor invocation. Formal schedule: POSITIVE/EXPIRE/NO_RESTART ×4 =12 fresh process-isolated sessions.

**D.** Formal12/12 complete; 12/12 worker exits0; expected atom sequence exact12/12; X server timestamps nondecreasing12/12; candidate equals independent raw-ledger oracle12/12. POSITIVE SATISFIED4/4; EXPIRE EXPIRED4/4; NO_RESTART EXPIRED4/4; task_input_events total0. Frozen audit: errors=[], five corruption controls reject. Separate postformal raw-only/source-hash audit: errors=[], 12/12 corruption controls reject. Formal invocations1, reruns0, replacements0, tuning0.

**C.** PropertyNotify timing is backend event-transport evidence, not semantic application-effect readiness. X server 32-bit timestamps are not treated as numerically comparable with Python monotonic time. Process isolation is a harness repair for Tk/X-server lifetime coupling, not a scientific treatment. The fixture is development-authored and the schedule is directed.

**U.** No cross-backend, wrap/reconnect, dropped-event completeness, model/task utility, token/latency benefit, human-tempo, production ABI or product claim. A PASS establishes only this scoped private-X11 transfer of the unchanged one-shot monitor.

## Preserved construction outcomes

1. Construction-01 STOP_ENVIRONMENT_PROPAGATION: historical runner restored XAUTHORITY before python-xlib connection; scientific rows saved0.
2. Construction-02 STOP_CASE_PROCESS_ISOLATION: same-process fresh-server reuse produced Tk/XIO; no row reconstructed or pooled.
3. Construction-03 STOP_CASE_PROCESS_ISOLATION: explicit display numbers still exposed Tk process-lifetime coupling; no row reconstructed or pooled.
4. Construction-04 PASS_CONSTRUCTION_ELIGIBLE after moving each fresh Xvfb/Tk case into a fresh Python process; scientific schedule/monitor/oracle/gates unchanged.

## Exact retained identities

- Formal result SHA256: `8cad9c2b4cf8c4c8c0a99d7f11739020c7d892a5ebe3fc630a7454f35c9c7ca9`
- Formal progress SHA256: `988f2b7064e4e217f8ae531f7fcbf782ca840ab62c5ce366aaa764c6aa360f77`
- Frozen audit SHA256: `53432afda41872dade81e59ba2120ea1284386e7bc7fcf60104f6f508ad0a1e6`
- Postformal audit v2 SHA256: `65cc7da3ed97b1adbc800d8aefcd7e8ccccb2508b771b7872a71a6495e989840`
- Evidence capsule SHA256: `d95d8249fc5dde6cdebc4e759ffe8d0e67f20dd825bba84a5f340281724bdeff`
- Expanded manifest: 65 files /127,292 member bytes; manifest SHA256 `3e52b236d639e2b51c1ad6802f3481fa758d6cc360aa67e57fe9071969d38d95`.

Use `restore_evidence.py <fresh-dir>` for byte-preserving restoration. Do not rerun the consumed formal allocation.
