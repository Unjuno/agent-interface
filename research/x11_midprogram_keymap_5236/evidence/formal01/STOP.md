# Issue #5236 formal01 — STOP record

Status: `STOP_PROVENANCE_OR_RUNNER` (`STOP_XVFB_SOCKET_ISOLATION`). This is an infrastructure failure, not a scientific result and not a PASS.

- Frozen base: `0a213fdb794d7c2498868fb109b1794465b70489`.
- Frozen command: `python -m research.x11_midprogram_keymap_5236.runner --output /tmp/agent-interface-issue5236-formal01-20260928T083100Z`.
- The single invocation began and blocked waiting for the Xvfb `-displayfd` line. At inspection, runner PID 217 had only child Xvfb PID 279. There was no fixture process, row directory, `setxkbmap` actor, or XTEST input.
- The pre-existing WSLg `/tmp/.X11-unix` was mode 0755 and contained its X0 socket. Xvfb stderr repeatedly said that the directory must be mode 1777 and that it could not bind its Unix listener.
- To stop only this allocation's stuck server, PID 279 received SIGTERM. The original runner exited with status 1. No retry or alternate startup command was used.
- The runner temporarily wrote a 66,677-byte `raw.json` under WSL `/tmp`; a subsequent WSL invocation could not see that file. Its exact bytes/hash and an independent audit are unavailable. The audit/corruption commands were not run because the freeze allowed them only after runner exit 0.
- The existing source, frozen hashes, #5236 plan, and this STOP are preserved unchanged. Any further investigation requires a separately frozen successor allocation with mount-namespace socket isolation and durable output outside `/tmp`.

Scope: this only establishes that the frozen private-Xvfb startup failed on this WSL host. It says nothing about the keymap hypothesis or X11 backend behavior.

Successor environment-isolation allocation: [Issue #5243](https://github.com/Unjuno/agent-interface/issues/5243). This is a new allocation and does not reopen formal01.
