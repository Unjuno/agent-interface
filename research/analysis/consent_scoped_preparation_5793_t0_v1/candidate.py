#!/usr/bin/env python3
"""Finite consent-scoped UI-preparation portfolio fixture for Issue #5793."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

ALLOC = 'consent-scoped-preparation-5793-t0-docker-20261001-01'


def receipt(preparation: str, app_generation: int, owner: str = 'task-owner') -> dict:
    return {
        'preparation': preparation,
        'owner': owner,
        'consent_scope': 'disposable-task-owned-session',
        'app_generation': app_generation,
        'expiry': 'end-of-frozen-sequence',
        'restoration_plan': 'restore-and-independent-snapshot',
    }


def repeated_family() -> dict:
    common = {'all_effects_exact': True, 'warning_visible_for_all_tasks': True, 'user_state_unchanged': True}
    return {
        'task_order': ['A1', 'A2', 'A3'],
        'arms': {
            'none': {**common, 'total_cost': 15, 'observations': 6, 'setup_cost': 0, 'restore_cost': 0, 'disposition': 'COMPLETE', 'restoration_complete': True},
            'per_task': {**common, 'total_cost': 18, 'observations': 3, 'setup_cost': 6, 'restore_cost': 3, 'disposition': 'COMPLETE', 'restoration_complete': True},
            'session': {**common, 'total_cost': 12, 'observations': 3, 'setup_cost': 2, 'restore_cost': 1, 'disposition': 'COMPLETE', 'restoration_complete': True, 'receipts': [receipt('show-panel-A', 7)]},
        },
    }


def heterogeneous_family() -> dict:
    common = {'user_state_unchanged': True}
    return {
        'task_order': ['A1', 'B1'],
        'arms': {
            'none': {**common, 'total_cost': 10, 'observations': 4, 'all_effects_exact': True, 'critical_warning_visible': True, 'consequential_actions_after_warning_hidden': 0, 'disposition': 'COMPLETE', 'restoration_complete': True},
            'per_task': {**common, 'total_cost': 12, 'observations': 2, 'all_effects_exact': True, 'critical_warning_visible': True, 'consequential_actions_after_warning_hidden': 0, 'disposition': 'COMPLETE', 'restoration_complete': True},
            'session': {**common, 'incurred_cost': 8, 'observations': 3, 'all_effects_exact': False, 'critical_warning_visible': False, 'consequential_actions_after_warning_hidden': 0, 'disposition': 'DEFERRED_SAFETY', 'restoration_complete': True, 'receipts': [receipt('show-panel-A-hide-warning-B', 9)]},
        },
    }


def fault_controls() -> dict:
    return {
        'partial_restore': {'disposition': 'UNKNOWN_RESTORE', 'restoration_complete': False, 'user_state_changed': True, 'task_effect_exact': True},
        'competing_edit': {'disposition': 'DEFERRED_STALE_GENERATION', 'start_generation': 11, 'observed_generation': 12, 'consequential_actions_after_generation_change': 0, 'restoration_complete': None},
        'callback_side_effect': {'disposition': 'REJECTED_COLLATERAL', 'user_state_changed': True, 'restoration_complete': False, 'callback_journal_changed': True},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--formal', action='store_true')
    args = parser.parse_args()
    out = Path('/work/out' if args.formal else '/work/construction')
    out.mkdir(parents=True, exist_ok=True)
    result = {
        'allocation': ALLOC,
        'formal_invocations': 1 if args.formal else 0,
        'construction_invocations': 0 if args.formal else 1,
        'reruns': 0,
        'scenario_order': ['repeated_same_target', 'heterogeneous_warning', 'controls'],
        'families': {
            'repeated_same_target': repeated_family(),
            'heterogeneous_warning': heterogeneous_family(),
        },
        'controls': fault_controls(),
    }
    raw = out / 'formal.json'
    raw.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
