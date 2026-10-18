import argparse
import hashlib
import json
from pathlib import Path

SOURCE_COMMIT = '743ae74ec5be2472ff27fa06fe13d5ecf8534de5'
CONTROLLER_SHA256 = '51ceed1ee329da2c64cf26300acddcf3e57b03ad8b193716709dcc0a95143607'
GUARD_SHA256 = '7be055c4bd68a1528f4b2b02b543435bd64465ea42d4452f5597d6dce08442a0'
LIMITS = [
    'live observation timing',
    'physical release',
    'useful feedback',
    'bounded recovery',
    'ammo or progress effect',
    'game outcome',
]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def file_sha256(path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def field(value, *keys):
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def audit(raw, root):
    errors = []
    assertion_count = 0

    def check(condition, label):
        nonlocal assertion_count
        assertion_count += 1
        if not condition:
            errors.append(label)

    controller_hash = file_sha256(root / 'research' / 'doom' / 'map01_overlap_controller_v39.py')
    guard_hash = file_sha256(root / 'research' / 'live_control' / 'observable_signal_guard_v2.py')
    hard = field(raw, 'hard_outcome')
    recovery = field(raw, 'recovery_guard_counterfactual')
    terminal = field(raw, 'cancel_terminal')
    terminal_release = field(terminal, 'release')
    fresh = field(raw, 'recovered_fresh_source')
    admission = field(raw, 'final_admission')

    check(field(raw, 'source_commit') == SOURCE_COMMIT, 'commit')
    check(field(raw, 'controller_sha256') == CONTROLLER_SHA256 == controller_hash, 'controller sha')
    check(field(raw, 'guard_sha256') == GUARD_SHA256 == guard_hash, 'guard sha')
    check(
        field(hard, 'status') == 'HARD_INVALIDATED'
        and field(hard, 'current_value') == 80
        and field(hard, 'hard_minimum') == 88,
        'hard crossing',
    )
    check(
        field(recovery, 'status') == 'SOFT_CHANGED'
        and field(recovery, 'current_value') == 96
        and field(recovery, 'keep_existing_policy') is True,
        'recovery',
    )
    check(field(raw, 'event_order') == ['executor_cancel', 'planner_interrupt'], 'order')
    check(
        field(terminal, 'status') == 'cancelled'
        and field(terminal_release, 'verified') is True
        and field(terminal_release, 'keys_down') == []
        and field(terminal_release, 'buttons_down') == [],
        'terminal release',
    )
    check(field(raw, 'drained_latest') == 12 and field(raw, 'drained_invalidation') is None, 'fresh source')
    check(
        fresh == {
            'sequence': 12,
            'health': 96,
            'ammo': 4,
            'cover_admission': 'admitted',
            'guard_source_sequence': 12,
            'guard_source_value': 96,
        },
        'fresh recovery admission',
    )
    check(
        field(raw, 'planner_answer_eligible') is True
        and field(admission, 'status') == 'REJECTED_POLICY_INVALIDATED'
        and field(admission, 'input_authority_admitted') is False
        and field(admission, 'grants_input_authority') is False
        and field(admission, 'executor_admission') is None
        and field(admission, 'action_validity') is None
        and field(admission, 'policy_invalidation', 'outcome', 'status') == 'HARD_INVALIDATED',
        'final admission',
    )
    check(
        field(raw, 'formal_allocation_invocations') == 0
        and field(raw, 'game_model_gui_os_input') is False,
        'scope',
    )

    return {
        'status': 'PASS_SCOPED_REPLAY' if not errors else 'FAIL',
        'independent_assertions': assertion_count,
        'errors': errors,
        'source_commit': field(raw, 'source_commit'),
        'case': field(raw, 'case'),
        'limits': LIMITS,
    }


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, default=package / 'results' / 'candidate.json')
    parser.add_argument('--output', type=Path, default=package / 'results' / 'audit-v2.json')
    parser.add_argument('--root', type=Path, default=package.parents[2])
    args = parser.parse_args()

    try:
        raw = read_json(args.candidate)
    except (OSError, json.JSONDecodeError) as error:
        result = {
            'status': 'FAIL',
            'independent_assertions': 0,
            'errors': [f'candidate read: {error}'],
            'source_commit': None,
            'case': None,
            'limits': LIMITS,
        }
    else:
        result = audit(raw, args.root.resolve())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True))
    return 1 if result['status'] == 'FAIL' else 0


if __name__ == '__main__':
    raise SystemExit(main())
