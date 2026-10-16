"""Observation-only recovery after a failed native window handoff."""
from copy import deepcopy


def review_source(previous, review):
    if review['status'] == 'reviewed':
        return review['observation']
    source = deepcopy(previous)
    source['review_recovery'] = {
        'status': 'observation_required',
        'allowed_decisions': ['observe', 'finish'],
        'image_scope': 'previous retained image; not a new capture or input source',
        'window_review': deepcopy(review),
        'input_replayed': False,
    }
    return source


def validate_recovery_decision(source, decision):
    if 'review_recovery' not in source:
        return
    observe = (set(decision) == {'source_sequence', 'interaction'}
               and decision['interaction'] == 'observe')
    finish = (set(decision) == {'source_sequence', 'finish'}
              and decision['finish'] is True)
    if not (observe or finish):
        raise ValueError('window review pending: only explicit observe or finish is accepted; no input')
