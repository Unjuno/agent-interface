"""Saved-only A03 reconstruction; never import or rerun the historical producer."""
import json
from pathlib import Path
import sys


SOURCE = 'f72cd82d62c9d9f3860d4fa40980c56618bf5aaf'
EMPTY = {'verified': True, 'keys_down': [], 'buttons_down': []}
CASES = {
    'cancelled-empty': ('cancelled', EMPTY, True),
    'completed-empty-race': ('completed', EMPTY, True),
    'expired-empty-race': ('expired', EMPTY, True),
    'interrupt-transport-error': ('cancelled', EMPTY, True),
    'failed-terminal': ('failed', EMPTY, False),
    'needs-decision-terminal': ('needs_decision', EMPTY, False),
    'missing-release': ('cancelled', {}, False),
    'unverified-release': ('cancelled', {**EMPTY, 'verified': False}, False),
    'held-key-release': ('cancelled', {**EMPTY, 'keys_down': ['space']}, False),
    'held-button-release': ('cancelled', {**EMPTY, 'buttons_down': ['left']}, False),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(data):
    require(data.get('format') == 'v39-interrupt-cancel-composition-a03-v1', 'format')
    require(data.get('source_main') == SOURCE, 'source')
    rows = data.get('cases')
    require(type(rows) is list and len(rows) == len(CASES), 'case count')
    ids = [row.get('case') for row in rows]
    require(all(type(name) is str for name in ids) and set(ids) == set(CASES),
            'exact unique frozen case inventory')
    accepted_count = 0
    for row in rows:
        name = row['case']
        status, release, accepted = CASES[name]
        failed_interrupt = name == 'interrupt-transport-error'
        outcome = 'request_error' if failed_interrupt else 'requested'
        require(row.get('status') == status and row.get('release') == release,
                f'{name}: frozen stimulus')
        require(row.get('interrupt_fails') is failed_interrupt and
                row.get('interrupt_outcome') == outcome, f'{name}: interrupt summary')
        require(row.get('expected_accept') is accepted and
                row.get('disposition') == ('accepted' if accepted else 'rejected'),
                f'{name}: disposition')
        require(row.get('old_answer_eligible') is False and row.get('old_answer') is None,
                f'{name}: old summary')
        fresh = {'thread_id': 'thread-1', 'answer_eligible': True,
                 'answer': {'action': 'fresh'}} if accepted else None
        require(row.get('fresh_result') == fresh, f'{name}: fresh summary')

        # These are producer-recorded logical events, not wire/physical timestamps.
        expected = [
            {'event': 'thread_started', 'thread_id': 'thread-1'},
            {'event': 'turn_started', 'thread_id': 'thread-1', 'turn_id': 'turn-1',
             'input': 'old observation'},
            {'event': 'planner_interrupt', 'thread_id': 'thread-1', 'turn_id': 'turn-1'},
            {'event': 'cover_cancel', 'op': 'cancel', 'id': 'cover-1'},
        ]
        events = row.get('events')
        require(type(events) is list, f'{name}: events')
        if not accepted:
            require(len(events) > 4 and events[4].get('event') == 'terminal_rejected' and
                    type(events[4].get('reason')) is str and bool(events[4]['reason']),
                    f'{name}: rejection witness')
            expected.append(events[4])
        expected.extend([
            {'event': 'interrupt_outcome', 'outcome': outcome},
            {'event': 'cover_terminal', 'status': status, 'release': release},
            {'event': 'turn_answer_arrived', 'thread_id': 'thread-1', 'turn_id': 'turn-1'},
            {'event': 'old_turn_result', 'status': 'completed',
             'answer_eligible': False, 'answer': None},
        ])
        if accepted:
            expected.extend([
                {'event': 'turn_started', 'thread_id': 'thread-1', 'turn_id': 'turn-2',
                 'input': 'fresh observation'},
                {'event': 'turn_answer_arrived', 'thread_id': 'thread-1', 'turn_id': 'turn-2'},
                {'event': 'fresh_turn_result', **fresh},
            ])
        require(events == expected, f'{name}: event inventory/order/summary disagreement')
        accepted_count += accepted
    return {'schema': 'v39-cover-cancel-saved-audit-v2', 'cases': len(rows),
            'accepted': accepted_count, 'rejected': len(rows) - accepted_count,
            'result': 'PASS_SAVED_CONSTRUCTION_RECONSTRUCTION',
            'physical_release': 'unverified', 'current_caller_bound': 'unverified',
            'producer_rerun': False}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: audit_v39_cancel_composition_saved_v2.py candidate.json')
    print(json.dumps(audit(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))))
