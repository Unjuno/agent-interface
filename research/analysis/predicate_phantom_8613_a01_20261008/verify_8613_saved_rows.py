"""Independently reconstruct the frozen #8613 safe-history predicate.

Read the archived rows, never execute archived code or extract archive paths.
The serial finite model and complete membership observations are assumptions.
"""
import hashlib
import itertools
import json
import sys
import tarfile

RAW_SHA = 'e6c4e05f105a8009abe3242da19f9d845bedbdc660cb334f30d4808441d218a7'
TEMPLATES = ('unique', 'distractor', 'multiple', 'none', 'disabled', 'other_scope', 'incomplete')
EVENTS = ('insert_B', 'insert_C', 'remove_A', 'remove_B', 'rename_B', 'enable_B',
          'replace_surface', 'unrelated', 'mark_incomplete', 'mark_complete')
ARMS = ('NODE_ONLY', 'ALWAYS_REQUERY', 'MEMBERSHIP_CERT')


def safe_history(kind, events):
    nodes = {'A': [True, 'Save', True, 'dialog', 0],
             'B': [False, 'Other', True, 'dialog', 0],
             'C': [False, 'Other', True, 'dialog', 0]}
    complete = kind != 'incomplete'
    if kind == 'distractor': nodes['B'][0] = True
    if kind == 'multiple': nodes['B'][:2] = [True, 'Save']
    if kind == 'none': nodes['A'][1] = 'Other'
    if kind == 'disabled': nodes['A'][2] = False
    if kind == 'other_scope': nodes['A'][3] = 'other'
    def members():
        return tuple(k for k, v in nodes.items() if v[0] and v[1] == 'Save' and v[2] and v[3] == 'dialog')
    initial = members()
    target = initial[0] if complete and len(initial) == 1 else None
    revision = nodes[target][4] if target else None
    stable = True
    for event in events:
        before, old_complete = members(), complete
        if event in ('insert_B', 'insert_C'):
            node = nodes[event[-1]]; node[:4] = [True, 'Save', True, 'dialog']; node[4] += 1
        elif event in ('remove_A', 'remove_B'):
            node = nodes[event[-1]]
            if node[0]: node[0] = False; node[4] += 1
        elif event == 'rename_B':
            node = nodes['B']
            if node[0]: node[1] = 'Other' if node[1] == 'Save' else 'Save'; node[4] += 1
        elif event == 'enable_B':
            node = nodes['B']
            if node[0]: node[2] = not node[2]; node[4] += 1
        elif event == 'replace_surface': stable = False
        elif event in ('mark_incomplete', 'mark_complete'): complete = event == 'mark_complete'
        elif event != 'unrelated': raise ValueError('unknown event')
        if members() != before or complete != old_complete: stable = False
    return bool(target and nodes[target][0] and nodes[target][4] == revision and
                stable and complete and members() == initial)


def verify(capsule):
    expected = ((kind, events) for kind in TEMPLATES for n in (2, 3, 4)
                for events in itertools.product(EVENTS, repeat=n))
    counts = {'rows': 0, 'safe': 0, 'NODE_ONLY_unsafe': 0,
              'ALWAYS_REQUERY_unsafe': 0, 'MEMBERSHIP_CERT_mismatch': 0}
    digest = hashlib.sha256()
    with tarfile.open(capsule, 'r:xz') as archive:
        member = archive.getmember('formal/rows.jsonl')
        if not member.isfile(): raise ValueError('raw member is not a file')
        with archive.extractfile(member) as raw:
            for index, (line, (kind, events)) in enumerate(zip(raw, expected, strict=True)):
                digest.update(line)
                row = json.loads(line)
                if row['index'] != index or row['template'] != kind or tuple(row['events']) != events:
                    raise ValueError('history mismatch at index %s' % index)
                decisions = row['decisions']
                if set(decisions) != set(ARMS) or any(type(decisions[a]) is not bool for a in ARMS):
                    raise ValueError('invalid decisions at index %s' % index)
                safe = safe_history(kind, events)
                counts['rows'] += 1; counts['safe'] += safe
                for arm in ('NODE_ONLY', 'ALWAYS_REQUERY'):
                    counts[arm + '_unsafe'] += decisions[arm] and not safe
                counts['MEMBERSHIP_CERT_mismatch'] += decisions['MEMBERSHIP_CERT'] != safe
    if digest.hexdigest() != RAW_SHA: raise ValueError('raw digest mismatch')
    if counts != {'rows': 77700, 'safe': 1277, 'NODE_ONLY_unsafe': 13465,
                  'ALWAYS_REQUERY_unsafe': 1266, 'MEMBERSHIP_CERT_mismatch': 0}:
        raise ValueError('reconstruction mismatch: %r' % counts)
    return counts


if __name__ == '__main__':
    if len(sys.argv) != 2: raise SystemExit('usage: python verify_8613_saved_rows.py RESULT_CAPSULE.tar.xz')
    print(json.dumps(verify(sys.argv[1]), sort_keys=True))
