# V39 cleanup forwarding bridge A03: down-call cleanup ordering

## H / T / D / C / U

- **H:** If a verified owner cleanup record is appended inside `owner.call("down")`, registering the returned admission's actuation context before draining lets the bridge emit the admission first, then exactly one contextual cleanup release; a later no-op up is suppressed.
- **T:** One deterministic in-memory owner-stub interleaving against the frozen A02 bridge and A03 successor. The stub appends the matching cleanup row before returning the down admission, then returns `NOOP_ALREADY_UP` for the later up. No real owner, GUI, OS input, game, or model is used.
- **D:** PASS only if the baseline reproduces unscoped cleanup plus duplicate no-op, and the successor emits admission then one same-actuation confirmed release, no no-op, and a neutral held-key set.
- **C:** This fixes the tested call-return ordering window in the synthetic bridge. It does not characterize every possible owner schedule.
- **U:** In-memory deterministic stub only; no live V39 deployment, X11, physical input, application effect, useful feedback, recovery, threat response, or MAP01 progress.

## Implementation

The successor registers actuation context from the returned down admission before draining newly appended owner records, and emits the admission before the cleanup release. A confirmed cleanup also removes the key from the bridge's held set. The frozen A02 source and its consumed outputs are preserved under `SOURCE/A02/`; the successor does not rerun either retained candidate.

## Reproduction

The frozen one-shot probe writes `RAW.json` and `RESULT.json` to a caller-provided output directory. Run `python3 build_freeze.py`, then `python3 probe_a03.py --out /tmp/a03-out`, `python3 audit_a03.py --out /tmp/a03-out`, and `python3 -m unittest -v test_a03.py`.
