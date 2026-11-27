# V39 Xvfb owner-close successor chain A08-A13

## H / T / D / C / U

- **H:** The exact current-main V4->V3->V12 owner path can release one admitted key on an isolated X server during wrapper close, verify server key-up, preserve a terminal owner-release receipt, and stop its owner thread.
- **T:** Successor one-shot probes A08-A13 frozen against `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. A13 runs one key against Xvfb `:136` with TCP confined to a private network namespace; the candidate and a separate raw-only auditor each run once.
- **D:** PASS_METHOD_SCOPED requires exact source hashes, matching KeyPress/KeyRelease at the intended window/keycode, observer key-up, verified terminal `owner_release(reason=close)` with empty keys, stopped thread, and Xvfb exit 0. Incomplete/setup traces are STOP, not success.
- **C:** The X server is synthetic. This measures a one-key shutdown path and server state only.
- **U:** No physical key state, target application consumption, task effect, useful feedback, latency distribution, threat reaction, recovery, or MAP01 outcome is established.

## Outcomes

- A08: STOP; python-xlib was extracted under WSL `/tmp`, which did not persist into the candidate invocation.
- A09: STOP; candidate hash guard correctly rejected `input_owner_v10.py` after its bytes were accidentally altered while generating the successor.
- A10: STOP; source preflight passed, but Xvfb setup rejected WSL's read-only `/tmp/.X11-unix` mode 0777 and reported missing `xkbcomp`.
- A11: NOT RUN; no candidate or auditor was invoked. A root permission change was refused by the read-only mount.
- A12: STOP; exact-main candidate reached Xvfb but the server exited on display `:134` with `Bad display name`; no input was admitted.
- A13: PASS_METHOD_SCOPED. Independent audit: `results/A13/AUDIT.json`, 11/11 checks true, zero errors. Raw SHA-256: `d7169e9547f6dabbb8c48ce7765b795b21ad1865944fe5d00d1ef940593fb221`. Audit SHA-256: `00518afd98191b0fcbb8424473eda032d95947071c7360638d45944df4b01b95`.

A13 observed one admitted `a` key (keycode 38), client KeyPress and KeyRelease at window 2097152, and an owner key-state sample from down to up bracketed by KeyRelease/XSync. Terminal cleanup was verified with `keys_down=[]`, `keys_unknown=[]`, no key-state errors, and `owner_thread_alive=false`. Its `key_release_intervals_ns` bracket is an X-server sample interval, not a physical or application-level duration.

## Runtime and isolation

The candidate used exact pinned source bytes for `input_owner_v10.py`, `input_owner_v12.py`, `input_transition_owner_v3.py`, and `input_transition_owner_v4.py`. A13 ran inside an isolated Linux network namespace, with loopback enabled, Xvfb TCP display `:136`, and Unix X sockets disabled. The only client address was `127.0.0.1:136`; no host display or game was used. Runtime Debian packages were downloaded and extracted under an external D: scratch directory; no system package installation occurred.

Per-run SHA-256 manifests are in each A08-A13 directory. A08-A10 and A12 STOP records are preserved without retry or overwrite; A11 has a freeze and explicit not-run status but no result leaf.
