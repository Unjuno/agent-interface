# A08 result — V39 owner close on real Xvfb

**Decision: `PASS_METHOD_SCOPED`.** A single `a` key was admitted by exact current-main InputOwner v12 through transition owner v4→v3 on TCP-disabled Xvfb `:130`. Calling the V4 wrapper's `close()` emitted a matching X KeyRelease to the client. The observer keymap was up; the terminal V12 `owner_release` record says `reason=close`, `verified=true`, `keys_down=[]`; the owner is closed and stopped with no live thread; Xvfb exited 0.

The frozen raw-only audit verified all required conditions with no errors. Raw SHA-256: `17eee08c9bde4fa8ac383919813b9e8e62871baf332a202b479fb8fcae11b69a`. Audit SHA-256: `c31efed7ff1f33a681b6d64fbe46d3eae8e853e1217afafe1fb20089e43884b2`. Candidate SHA-256: `004308f92985c7af5ce7a45a4d17b45fc2f91325849e08bbbf2c22b66db095bd`.

Reproduction command (one-shot candidate; completed):

```sh
wsl -e bash -lc 'cd /mnt/c/Users/junny/Documents/Codex/2026-10-03/new-chat-3/work/agent-interface-v39-perkey-a03 && PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/v39_owner_close_xvfb_a08_20261005/SOURCE/candidate.py --out research/doom/v39_owner_close_xvfb_a08_20261005/results/A08 --display :130'
```

Then the raw-only auditor was invoked once using `SOURCE/audit.py`, `FREEZE.json`, `RAW.json`, and `SOURCE/candidate.py`; it wrote `results/A08/AUDIT.json`. Exact current-main source base: `ff13baf57d5f1c12819151e668b92cb6db4a7c1c`.

This is one synthetic X-server shutdown-path result only. It supports verified release on owner close for this V12/V4 composition and environment. It does not establish physical key state, delivery to a real desktop/game app, broader failure-rate guarantees, latency under load, or Issue #59 completion. A06's 30-batch trace separately retained partial ordering evidence but remains STOP because wrapper cleanup was not verified; A05/A07 remain setup/invocation STOPs.
