# MAP01 HUD signal value-domain guard A01

## H / T / D / C / U

**H — hypothesis.** A parsed health value must be within the controller's
declared MAP01 health domain (1–200), and ammo must fit the exact three-slot
HUD representation (0–999), before source refresh or action admission can
accept it. Previously the refresh gate checked only lower bounds, while the
action contract accepted any nonnegative integer.

**T — test.** On CPU with synthetic readers, test lower/upper boundaries,
out-of-domain health/ammo, booleans and non-integers. Confirm that invalid
observed values refuse before a passive refresh and that an invalid refreshed
frame cannot be bypassed by a later positive frame. Exhaustively enumerate
integer inputs from -1 through 1001 against the declared ranges. Run the
existing source-refresh, action-contract, controller-cleanup, and V39 controller
tests.

**D — gate and outcome.** PASS only if both domain endpoints are admitted,
every value outside the domain and every non-integer is refused, refresh never
continues past an observed invalid value, action contracts reject invalid
source values, and existing focused tests remain green. The pre-change run
failed on health 201 and ammo 1000 at both refresh gates and admitted source
health 0 / 201 and ammo 1000 in the action contract. After the fix the focused
suite passes: 3 domain, 13 refresh, 6 action-contract, 5 cleanup, and 2 V39
controller tests.

**C — controls and scope.** This checks the source/action numeric domain only.
It leaves the exact glyph matcher and its templates unchanged. The 1–200
health limit matches the existing authored health-policy schema; the 0–999
ammo limit follows the existing three-slot HUD reader. No game, model, GPU,
GUI, network, or live input was used.

**U — unknowns.** This does not test false glyph matches within the valid
range, live WAD/frame extraction, actual recovery efficacy, useful feedback,
per-key timing, or #59's matched live threat-control gate. Out-of-domain values
from a different game or modified HUD are rejected by this MAP01-specific
contract.

## Current-main evidence boundary

Current main also contains cleanup repair #7594. Its existing focused tests
were included after rebasing this change.

PR #7588 has retained one actual recovery: typed sequence 59 was UNKNOWN;
an observe-only refresh produced sequence 60 with health 91/ammo 45 and a
matching completed empty-release receipt; the following action turn completed.
Its later scorer reports zero kills/reward and no map exit, so task-useful
recovery remains HOLD. The saved run did not encounter or test out-of-domain
health/ammo values. This patch is a separate deterministic admission-boundary
repair; it does not change or regrade that actual recovery result.

## Change

Added a pure-Python shared value-domain predicate and applied it at both the
bounded passive refresh boundary and the action-source contract. Invalid
observed values fail closed; they are not treated as UNKNOWN and do not get a
chance to be replaced by a later favorable frame. Existing valid signals and
the refresh budget are unchanged.

## Reproduction

Run from `research/doom`:

```powershell
python -m unittest test_doom_signal_value_domain_v1 test_source_refresh_v1 test_doom_action_validity_contract_v1 test_controller_failure_cleanup_v1 test_map01_overlap_controller_v39 -v
python -m py_compile doom_signal_value_domain_v1.py doom_source_refresh_v1.py doom_action_validity_contract_v1.py test_doom_signal_value_domain_v1.py test_source_refresh_v1.py test_doom_action_validity_contract_v1.py
```

`TEST_OUTPUT.txt` retains the passing test command output (29 total tests).
`FREEZE.txt` pins the current-main base, changed sources, tests, and result
artifact.
