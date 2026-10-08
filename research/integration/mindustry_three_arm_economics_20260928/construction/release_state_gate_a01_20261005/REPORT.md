# Release-state gate A01 (2026-10-05)

## Finding

The pinned `target_socket_submit_v1.py` candidate marked an action `released: true` when its terminal receipt omitted `keys_down` or `buttons_down`, and when either set reported held input. The frozen seven-case in-memory probe accepted the empty verified control and also falsely accepted four unsafe/malformed receipts. The independent auditor classified this as `PASS_GAP_REPRODUCED`.

The additive adapter fix now requires `verified is True` and explicitly present empty `keys_down` and `buttons_down`. It accepts the producer metadata envelope (`event`, `reason`, `verified_ns`, and `valid_until_ns`) with type/value checks, and rejects unknown fields. The regression test covers a valid control, held key, held button, missing keys field, and missing buttons field.

## H/T/D/C/U

- **H:** A successful terminal could be treated as released despite missing or nonempty held-input state.
- **T:** Loaded only the frozen Git blob `ffaa64cb04f0457c11e52393b32a5ba9b2b733b0` from commit `8ff7afed76c1d81eabac9d0c37d4191b352045a4`; injected seven deterministic responses through the adapter's in-memory exchange. No socket, GUI, game, model, Docker, or operating-system input was used.
- **D:** `PASS_GAP_REPRODUCED` when any unsafe/malformed case was accepted. The original adapter produced four false accepts: held key, held button, omitted `keys_down`, omitted `buttons_down`.
- **C:** The action, command receipt, authority, terminal status, and cursor stayed fixed; only release fields varied. `audit.py` checks raw outcomes separately from the candidate.
- **U:** One Windows host with Python 3.12.14 and a synthetic adapter boundary. The experiment does not assess the actual release producer, transport, physical release, Mindustry task effects, or the formally allocated economics trial.

## Repair validation

After the regression was observed failing against the frozen candidate, the adapter was changed to fail closed on missing, unknown, wrongly typed, unverified, or nonempty held-input state. The Mindustry integration package has 122 tests passing in normal mode and 122 passing under `-O`; each mode reports two expected AF_UNIX skips on this Windows host. `py_compile` and `git diff --check` both exit 0. Logs and receipts are preserved in this directory. `REPAIR-RESULT-v1.json` and `full-discover-no-tests.log` preserve earlier command/setup errors rather than concealing them.

## Limits and next step

This is an adapter contract repair based on a synthetic terminal payload. The upstream producer source path is statically inspected and its owner_release envelope is exercised synthetically. Runtime execution, X11 state, and physical release remain untested. The #5130 formal Docker/game allocation remains a separate authorization gate. This result is not live, formal, economics, or product-readiness evidence. Before that run, integrate and verify the producer contract under the exact assigned slot, then execute the preregistered protocol and independent raw audit.

## Replay

Run `python -B run_probe.py` in a checkout containing the frozen Git object, then `python -B audit.py raw.json`. The first command reads the immutable candidate blob and writes its raw observations to stdout; save those bytes as `raw.json`. The second command exits zero for either an expected reproduced gap or a clean contract result, and nonzero for malformed evidence or an unexpected disposition.
