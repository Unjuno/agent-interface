from __future__ import annotations

def reduce_history(scope: str, events: list[dict]) -> dict:
    action_seq = 0
    actions: dict[str, dict] = {}
    evidences: dict[str, dict] = {}
    effects = 0
    rows = []
    for op in events:
        kind = op['kind']
        try:
            if kind == 'SELF_ACTION':
                aid = op['action_id']; relevant = op['relevant']
                if not isinstance(aid, str) or not aid or not isinstance(relevant, bool):
                    raise ValueError('oracle_bad_action')
                if aid in actions:
                    if actions[aid]['relevant'] != relevant:
                        raise ValueError('oracle_conflicting_action')
                    res = {'result': 'DUPLICATE_NOOP', 'action_seq': actions[aid]['seq']}
                else:
                    action_seq += 1
                    actions[aid] = {'seq': action_seq, 'relevant': relevant}
                    res = {'result': 'RECORDED', 'action_seq': action_seq}
                rows.append({'kind': kind, 'ok': True, 'result': res})
            elif kind == 'OBSERVE':
                eid = op['evidence_id']; vg = op['visual_guard']; cover = op['covered_action_seq']
                if not isinstance(eid, str) or not eid or not isinstance(vg, bool) or not isinstance(cover, int) or cover < 0:
                    raise ValueError('oracle_bad_evidence')
                if cover > action_seq:
                    raise ValueError('oracle_future_cover')
                ev = {'evidence_id': eid, 'scope': scope, 'visual_guard': vg, 'covered_action_seq': cover}
                if eid in evidences:
                    if evidences[eid] != ev:
                        raise ValueError('oracle_conflicting_evidence')
                    res = {'result': 'DUPLICATE_NOOP', 'evidence_id': eid}
                else:
                    evidences[eid] = ev
                    res = {'result': 'PUBLISHED', 'evidence_id': eid}
                rows.append({'kind': kind, 'ok': True, 'result': res})
            elif kind == 'TRY_EFFECT':
                eid = op['evidence_id']; ordinary = op['ordinary_authority']; pscope = op.get('presented_scope', scope)
                if not isinstance(eid, str) or not eid or not isinstance(ordinary, bool):
                    raise ValueError('oracle_bad_effect')
                ev = evidences.get(eid)
                latest_rel = max([a['seq'] for a in actions.values() if a['relevant']], default=0)
                admitted = True; reason = 'ADMIT'
                if pscope != scope:
                    admitted = False; reason = 'WRONG_SCOPE'
                elif ev is None:
                    admitted = False; reason = 'EVIDENCE_MISSING'
                elif not ordinary:
                    admitted = False; reason = 'ORDINARY_AUTHORITY_FALSE'
                elif not ev['visual_guard']:
                    admitted = False; reason = 'VISUAL_GUARD_FALSE'
                elif latest_rel > ev['covered_action_seq']:
                    admitted = False; reason = 'WAIT_FRESH_PUBLICATION'
                if admitted:
                    effects += 1
                rows.append({'kind': kind, 'ok': True, 'result': {'admitted': admitted, 'reason': reason, 'evidence_id': eid}})
            else:
                raise ValueError('oracle_bad_kind')
        except ValueError as exc:
            rows.append({'kind': kind, 'ok': False, 'error': str(exc)})
    latest_rel = max([a['seq'] for a in actions.values() if a['relevant']], default=0)
    return {
        'rows': rows,
        'state': {
            'scope': scope,
            'action_seq': action_seq,
            'actions': {k: actions[k] for k in sorted(actions)},
            'evidences': {k: evidences[k] for k in sorted(evidences)},
            'effects': effects,
            'latest_relevant_action_seq': latest_rel,
        },
    }
