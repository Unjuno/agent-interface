# #1707 Report — real XTerm phase overlap v1

**Original decision: `FAIL_REAL_XTERM_PHASE_OVERLAP` (audit logic failure retained; no rerun).**

## Formal first outcome
All 24 frozen XTerm/Xvfb cases executed once with no case-level process failure. The aggregate execution result was mechanically favorable:

| arm | n | median wall ms | terminal keys neutral |
|---|---:|---:|---:|
| serial_independent | 6 | 320.8507305 | 6/6 |
| overlap_independent | 6 | 168.087279 | 6/6 |
| serial_shared | 6 | 326.4401545 | 6/6 |
| overlap_shared_negative | 6 | 173.2362825 | 6/6 |

The retained aggregate gives independent-arm median reduction 152.7634515 ms and overlap/serial ratio 0.5238799947, inside the preregistered >=100 ms and <=0.65 gates.

The raw first outcomes also contain the expected final XTerm titles: the three correctness arms end A_DONE/B_DONE, while the deliberately unsafe shared-file overlap arm ends B_DONE/B_DONE. These observations are retained raw evidence, not a promoted PASS from this v1 audit.

## Why the original audit failed
The frozen auditor emitted 12 `serial_order:*` errors, one for every serial case. Inspection of the retained timeline exposes a diagnostic selection bug:

1. serial A reaches a genuine `done` event (`A_DONE`);
2. only then does B `input_begin` occur, satisfying the preregistered serial ordering;
3. after B starts, the runner records a redundant `done_already` diagnostic for A because A is still already terminal;
4. the auditor's `terminal_t()` selected the **last** event among `done|done_already`, so it used this later diagnostic instead of A's first terminal transition;
5. the auditor therefore falsely evaluated B input as preceding A terminal.

For example, retained case `serial_independent-02` records A `done` at 1715666770080 ns and B `input_begin` at 1715666878729 ns, followed later by A `done_already` at 1715674554610 ns. The original auditor used the last timestamp and raised `serial_order`.

No formal case is rerun, replaced, pooled or relabeled here. The original `AUDIT.json` remains the authoritative v1 audit result: FAIL.

## Integrity
Pre-formal sources were frozen before the single formal invocation. `FREEZE.json` records formal output absence, budget=1, reruns=0, replacements=0 and tuning_after_freeze=0.

Postformal SHA-256:
- `RAW_CASES.json`: `6426b6425764adc585585eff915faea504d1ddabac38ae34720660e277ce37f8`
- `RESULT.json`: `07c44477c1e1a4ebf032ebd6443bb2bc7d8b0fab8e5a1324b7500780182946e0`
- `AUDIT.json`: `2fa51e9e8f4c8830a1ab101d37922f1a3bd7272d3932ff4667402c562006ed75`

The 69,735-byte raw ledger is retained losslessly as deterministic gzip+base64. `restore_raw.py` verifies the reconstructed raw SHA before writing `RAW_CASES.json`.

## Successor boundary
A successor may change only the independent audit interpretation: use the **first observed terminal transition** per surface, not the later `done_already` diagnostic. It must consume this exact raw SHA, issue no X11/XTEST/task input, preserve every v1 source/result byte, and independently re-evaluate all original H/T/D gates. If any non-audit gate fails, the successor must not promote the mechanism.

## Limits
Even a successful audit repair would remain scoped to Linux/Xvfb/XTEST, XTerm(398), bash, a 150 ms delay and one shared-file negative control. No model/token/human-tempo/cross-platform/production claim follows.
