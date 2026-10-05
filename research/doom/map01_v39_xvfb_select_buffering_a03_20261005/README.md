# Xlib buffered-event readiness diagnostic A03

## H / T / D / C / U

**H.** A synchronous `query_keymap()` on the same Python-Xlib connection that owns the selected event window can read the X socket through the event bytes, place the event in Xlib's in-process queue, and leave the underlying fd not readable to `select()`.

**T.** In private Xvfb `:189`, compare three single-pair cases: (1) select the event-owning connection before querying; (2) call `query_keymap()` on that same connection before select; and (3) call `query_keymap()` on a separate connection before select on the event owner. The same-owner event connection creates the focused window, selects KeyPress/KeyRelease, and is the fd passed to `select()`. A separate driver sends synthetic XTEST events.

**D.** All six expected edges were received with exact event type, keycode 38 (`a`), and target window `2097152`. For select-first, both press and release fds were ready. For same-connection-query-first, both fds were not ready while Xlib already had one pending event; `query_keymap()` observed down/up state correctly. For separate-query-connection-first, both event-owner fds were ready. The independent raw audit reports `PASS_METHOD_SCOPED`, 0 errors, and verifies Xvfb exit 0/stopped.

**C.** This reproduces the buffered-event mechanism proposed in the open review on PR #7771 under the equivalent Xvfb/Python-Xlib arrangement: synchronous same-connection queries can consume kernel readability without consuming the event from Xlib's user-space queue. A separate query connection preserves event-owner fd readiness in this diagnostic.

**U.** It does not establish that this is the sole cause of PR #7771's A03 timeout or validate the integrated controller, because no game, model, pending controller loop, or original frozen candidate ran. It is a synthetic Xvfb construction result only; no claim about physical input, threat response, task effect, recovery, safety, or MAP01 completion.

## Provenance and execution

- Frozen probe: `probe.py`, SHA-256 `26969978bfdbde8275084856e35f64f48d168a7b0338328507aaa9f17d6411ac`.
- Freeze/source identity: `FREEZE.json`; current `main` at preregistration `a9352dc53c783f1501046d762bc36c34bc6ab480`; upstream A03 candidate reference is recorded there.
- Raw result: `evidence/RAW.json`, SHA-256 `7a4dab4690f6c0736adb3582bd246dbf11c8572b31f9855e5841327e1a65ea83`.
- Independent auditor: `audit.py`; its raw decision is `evidence/AUDIT.json`.
- Runtime: WSL Ubuntu host, Python 3.12.3, python-xlib 0.33, Xvfb package `2:21.1.12-1ubuntu1.6`; private display `:189`. This A03 used the installed WSL Xvfb/Xlib because the already-running WSLc sessions had not yielded output and the available local clone could not finish its sparse checkout. It was not a Docker/WSLc run. Candidate code makes no network calls; the OS network was not isolated.
- Command: `wsl.exe -d Ubuntu -- python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_research_xvfb_buffering_a03_20261005/probe.py`
- Auditor command: `wsl.exe -d Ubuntu -- python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_research_xvfb_buffering_a03_20261005/audit.py`
- A01 STOP and invalid A02 PASS-labelled output are documented separately in `evidence/PRIOR_ATTEMPTS.md`; neither is pooled into A03.

This is a diagnostic follow-up, not a rerun or replacement of PR #7771's A03 allocation. That original STOP remains unchanged.

## Audit identity correction (2026-10-05)

The retained `evidence/AUDIT.json` is the original audit-v1 result and remains unchanged. Review found that audit-v1 accepted a mutation that changed both the claimed keycode and matching event detail while recomputing the raw digest. `evidence/AUDIT_EXPECTATIONS_V2.json` and `audit_v2.py` add a corrective, post-run identity contract: the frozen probe asks for keysym `a`, and this retained run reports keycode 38 and target window 2097152. These values were **not** part of the original preregistration freeze; this post-run correction does not upgrade the experiment's independence or scientific scope.

`test_audit_v2.py` recomputes the digest over mutated raw bytes and confirms that changing the event keycode or target window fails the v2 identity check. The v2 report is `evidence/AUDIT_V2.json`. The original raw result, v1 auditor, and v1 report are preserved.
