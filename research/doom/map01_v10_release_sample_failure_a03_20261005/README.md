# V10 release-sampling failure A03

Supplemental fake-X regression for PR #7962. A failed keyboard-state query must not prevent best-effort release of a pointer button already observed down. If the final keyboard state remains unavailable, the owner must record that state as unknown and fail closed.

## H / T / D / C / U

- **H:** A `query_keymap()` exception can interrupt cleanup after `query_pointer()` has already shown a touched wheel button down, skipping the button retry and leaving no `owner_release` receipt.
- **T:** Run the same five fake-X owner tests against the frozen current-main V10 source and the PR candidate. The tests include a one-time keymap query failure and a persistent query failure while a wheel-button release is dropped.
- **D:** Current main is expected to fail the new mixed-failure cases. The candidate must recover the button after a transient query failure and, for a persistent query failure, retry the button, record unknown key state, and return an unverified error.
- **C:** Fake X only. This does not establish X server, physical input, application, GUI, or game behavior.
- **U:** Live V39 exposure, recovery timing, useful feedback, and MAP01 progress remain untested.

## Retained result

The frozen current-main source failed four of five tests (three assertion failures and one error); the PR candidate passed all five in normal and optimized Python. The candidate records separate keymap and pointer-state certainty. A final unavailable keymap is represented in `keys_unknown`, makes `verified` false, and raises after the independently sampled pointer input has received its bounded retry.

`FREEZE.json` binds the baseline and candidate source/test bytes. `raw/` retains both modes. `audit.py` validates these retained bytes and outputs without invoking X11. Run `python audit.py` to verify the package. `run.py` replays the synthetic matrix in temporary directories and leaves the retained outputs untouched.

No real X11 server, OS input, game, model, live allocation, or physical-release claim is included.
