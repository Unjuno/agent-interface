# Current-main rescue and preservation guard

## H — Hypothesis

The retained A03 result can be salvaged as additive evidence while preventing normal revalidation commands from replacing its one-shot audit and freeze.

## T — Local tests

- The original one-shot A03 candidate was not rerun.
- `test_preservation.py` invokes the additive stdout-only audit and the guarded freeze entry point, then byte-compares the frozen `results/AUDIT.json` and `FREEZE.json` before and after.
- The original `SHA256SUMS` remains the immutable one-shot package manifest; `SHA256SUMS_V2` covers only the additive wrappers, test, and preservation documentation.

## D — Data and scope

The historical `audit.py`, `build_freeze.py`, `FREEZE.json`, `results/AUDIT.json`, raw A03 output, and original manifest are retained byte-for-byte. The README now explicitly warns that the historical commands overwrite frozen artifacts and points to guarded entry points.

## C — Caveats

This verifies artifact preservation and audit CLI behavior only. It does not rerun candidate, game, model, GUI, OS input, or formal allocation, and makes no live-control efficacy claim.

## U — Remaining gate

This successor remains draft until independent review and repository CI pass. The source PR and branch remain untouched.
