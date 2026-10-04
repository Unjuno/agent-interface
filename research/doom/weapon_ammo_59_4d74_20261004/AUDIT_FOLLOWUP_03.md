# Weapon/ammo audit follow-up 03

## H / T / D / C / U

**H.** The nearest scorer/API row used to compare against the initial typed HUD capture must be independently coherent, not merely labeled `coherent_tic`. It must have an exact boolean `true` coherence flag, ordered integer sample bounds, equal integer tic endpoints, and finite numeric variables.

**T.** On a temporary copy of the retained `00-coast` fixture, mutate the nearest row separately to (1) unequal tic endpoints, (2) reversed sample bounds, and (3) a non-finite diagnostic variable. Each must change the successor auditor from `PASS_HUD_WEAPON_AMMO_BINDING_SCOPED` to `HOLD_AUDIT_CHECK_FAILED`. The unmodified committed fixture remains the positive control.

**D.** All three mutated cases hold; the retained fixture remains scoped PASS. After parent PR #7631 advanced, the combined follow-up 01/02/03 focused suite passes 16/16 on parent head `367df9288913ee142a216403c740e4072c13d7c3` plus this successor. The new mutation tests were observed failing against the incomplete follow-up-03 wrapper before their corresponding checks were added. `py_compile` and `git diff --check` pass.

**C.** A trustworthy producer may guarantee that `coherent_tic=true` implies ordered sampling and equal tics. This auditor must not silently rely on that implication when the row is outside the scored-window validation; independently checking the values is cheap and makes the retained-data predicate explicit.

**U.** This is synthetic mutation testing and a post-result audit of one retained selected-weapon/ammo fixture. It does not show that the original run contained an incoherent row, nor prove simultaneous HUD/API truth, damage exposure, useful feedback, recovery efficacy, controller trust/adoption, live gameplay, or MAP01 completion. The implementation imports the preceding follow-up-02 auditor and is stacked after PR #7631; integrate only after that dependency is reviewed and merged.

## Reproduction

From this directory:

```sh
python3 -m unittest -v test_audit_weapon_ammo_followup_01.py test_audit_weapon_ammo_followup_02.py test_audit_weapon_ammo_followup_03.py
python3 audit_weapon_ammo_followup_03.py
python3 -m py_compile audit_weapon_ammo_followup_01.py audit_weapon_ammo_followup_02.py audit_weapon_ammo_followup_03.py test_audit_weapon_ammo_followup_01.py test_audit_weapon_ammo_followup_02.py test_audit_weapon_ammo_followup_03.py
git diff --check
```

The structured outcome and frozen input/source hashes are in `AUDIT_FOLLOWUP_03_RESULT.json`. Container execution was attempted only as an environment check: Docker reports server 29.4.0, but image inventory fails on a containerd content blob with `operation not supported`. Therefore this result is host-Python validation, not a container PASS. No game/model/GUI/input allocation ran.
