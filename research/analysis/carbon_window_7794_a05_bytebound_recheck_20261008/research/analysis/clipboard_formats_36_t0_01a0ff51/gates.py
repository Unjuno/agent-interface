"""Fixture-scoped metadata admission and post-effect assessment; no authority."""


def precheck(arm, expected, observed):
    if observed is None or type(observed.get('generation')) is not int or (observed.get('summary') is None and not observed.get('formats')):
        return 'HOLD_RESOURCE'
    for key in ('generation', 'owner', 'scope', 'summary'):
        if expected[key] != observed.get(key):
            return 'REJECT_DEPENDENCY'
    if arm == 'manifest' and expected['formats'] != observed.get('formats'):
        return 'REJECT_DEPENDENCY'
    return 'ELIGIBLE'


def postcheck(attempted, consumed, effect, contract, *, require_format):
    if not attempted:
        return 'NO_EFFECT'
    if require_format:
        if len(consumed) != 1:
            return 'HOLD_FORMAT'
        if consumed[0] not in contract['formats']:
            return 'WRONG_FORMAT'
    if effect['text'] != contract['text'] or (contract['bold'] is not None and effect['bold'] is not contract['bold']):
        return 'VERIFIED_WRONG'
    return 'VERIFIED_CORRECT'
