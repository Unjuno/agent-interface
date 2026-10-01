#!/usr/bin/env python3
"""Independent raw-only audit for the finite Issue #5793 portfolio fixture."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

RAW = Path('/work/out/formal.json')
EXPECTED_REPEAT_COSTS = {'none': 15, 'per_task': 18, 'session': 12}
EXPECTED_HETERO_COSTS = {'none': 10, 'per_task': 12}


def validate(doc: dict) -> list[str]:
    errors = []
    if doc.get('formal_invocations') != 1 or doc.get('reruns') != 0:
        errors.append('allocation_count')
    fam = doc.get('families', {})
    if set(fam) != {'repeated_same_target', 'heterogeneous_warning'}:
        errors.append('family_denominator')
        return errors
    repeat = fam['repeated_same_target']
    if repeat.get('task_order') != ['A1', 'A2', 'A3']:
        errors.append('repeat_schedule')
    arms = repeat.get('arms', {})
    if set(arms) != {'none', 'per_task', 'session'}:
        errors.append('repeat_arm_set')
    for name, cost in EXPECTED_REPEAT_COSTS.items():
        row = arms.get(name, {})
        if row.get('total_cost') != cost:
            errors.append('repeat_cost:' + name)
        if row.get('all_effects_exact') is not True or row.get('user_state_unchanged') is not True:
            errors.append('repeat_safety:' + name)
        if row.get('warning_visible_for_all_tasks') is not True:
            errors.append('repeat_warning:' + name)
        if row.get('restoration_complete') is not True or row.get('disposition') != 'COMPLETE':
            errors.append('repeat_restore:' + name)
    if not (arms.get('session', {}).get('total_cost', 10**9) < arms.get('none', {}).get('total_cost', -1)
            and arms.get('session', {}).get('total_cost', 10**9) < arms.get('per_task', {}).get('total_cost', -1)):
        errors.append('session_not_lower_than_both_controls')
    h = fam['heterogeneous_warning']
    if h.get('task_order') != ['A1', 'B1']:
        errors.append('heterogeneous_schedule')
    harms = h.get('arms', {})
    if set(harms) != {'none', 'per_task', 'session'}:
        errors.append('heterogeneous_arm_set')
    for name, cost in EXPECTED_HETERO_COSTS.items():
        if harms.get(name, {}).get('total_cost') != cost:
            errors.append('heterogeneous_cost:' + name)
    for name in ('none', 'per_task'):
        row = harms.get(name, {})
        if row.get('all_effects_exact') is not True or row.get('critical_warning_visible') is not True:
            errors.append('heterogeneous_control_invalid:' + name)
    unsafe = harms.get('session', {})
    if unsafe.get('disposition') != 'DEFERRED_SAFETY' or unsafe.get('critical_warning_visible') is not False:
        errors.append('warning_hiding_not_rejected')
    if unsafe.get('consequential_actions_after_warning_hidden') != 0 or unsafe.get('all_effects_exact') is not False:
        errors.append('warning_hidden_effect_gate')
    if 'total_cost' in unsafe or unsafe.get('incurred_cost') != 8:
        errors.append('unsafe_partial_cost_misrepresented_as_completion')
    controls = doc.get('controls', {})
    partial = controls.get('partial_restore', {})
    if partial.get('disposition') != 'UNKNOWN_RESTORE' or partial.get('restoration_complete') is not False:
        errors.append('partial_restore_misreported')
    stale = controls.get('competing_edit', {})
    if (stale.get('disposition') != 'DEFERRED_STALE_GENERATION'
            or stale.get('observed_generation') == stale.get('start_generation')
            or stale.get('consequential_actions_after_generation_change') != 0):
        errors.append('competing_edit_not_blocked')
    collateral = controls.get('callback_side_effect', {})
    if (collateral.get('disposition') != 'REJECTED_COLLATERAL'
            or collateral.get('user_state_changed') is not True
            or collateral.get('restoration_complete') is not False):
        errors.append('collateral_misreported_as_restored')
    for famrow in fam.values():
        receipt_rows = famrow.get('arms', {}).get('session', {}).get('receipts', [])
        if not receipt_rows:
            errors.append('session_receipt_missing')
        for receipt in receipt_rows:
            if (receipt.get('owner') != 'task-owner'
                    or receipt.get('consent_scope') != 'disposable-task-owned-session'
                    or receipt.get('restoration_plan') != 'restore-and-independent-snapshot'
                    or not receipt.get('expiry')):
                errors.append('receipt_scope_incomplete')
    return errors


def main() -> None:
    raw = RAW.read_bytes()
    doc = json.loads(raw.decode('utf-8'))
    errors = validate(doc)
    mutations = {}
    changed = copy.deepcopy(doc)
    changed['families']['repeated_same_target']['arms']['session']['total_cost'] = 15
    mutations['benefit_erasure_rejected'] = bool(validate(changed))
    partial = copy.deepcopy(doc)
    partial['controls']['partial_restore']['restoration_complete'] = True
    mutations['partial_restore_claim_rejected'] = bool(validate(partial))
    stale = copy.deepcopy(doc)
    stale['controls']['competing_edit']['consequential_actions_after_generation_change'] = 1
    mutations['stale_action_rejected'] = bool(validate(stale))
    hidden = copy.deepcopy(doc)
    hidden['families']['heterogeneous_warning']['arms']['session']['consequential_actions_after_warning_hidden'] = 1
    mutations['warning_hidden_action_rejected'] = bool(validate(hidden))
    if not all(mutations.values()):
        errors.append('mutation_control_escape')
    result = {
        'status': 'PASS_METHOD_SCOPED' if not errors else 'FAIL_METHOD_OR_EVIDENCE',
        'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'errors': errors,
        'mutation_controls': mutations,
        'claim_boundary': 'finite synthetic simulator only; no live GUI, human consent, or general efficiency claim',
    }
    (RAW.parent / 'audit.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
