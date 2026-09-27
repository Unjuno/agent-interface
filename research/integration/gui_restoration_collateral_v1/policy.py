"""Read-only live-receipt adapter; the #2076 reducer is unchanged."""
from predecessor import reduce_outcome


def classify(initial, terminal, receipt):
    expected = initial['identity']
    actual = receipt.get('identity', {})
    bound = (type(actual.get('generation')) is int and
             type(expected.get('generation')) is int and actual == expected and
             terminal['identity'] == expected)
    collateral = receipt.get('collateral_preserved')
    if collateral is not None and type(collateral) is not bool:
        collateral = None
    primary = type(initial['value']) is type(terminal['value']) and initial['value'] == terminal['value']
    return {'primary_restored': primary, 'collateral_preserved': collateral,
            'identity_current': bound, 'outcome': reduce_outcome(primary, collateral, bound),
            'primary_only': 'COMPLETE_SUCCESS' if primary else 'FAILURE',
            'authority': False}
