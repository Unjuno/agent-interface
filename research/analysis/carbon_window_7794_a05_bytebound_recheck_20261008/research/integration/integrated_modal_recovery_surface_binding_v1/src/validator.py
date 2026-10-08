class RecoveryRejected(Exception):
    pass

def _common(receipt):
    if receipt.get('authority') != 'none':
        raise RecoveryRejected('authority')
    if receipt.get('task_input_granted') is not False:
        raise RecoveryRejected('task_input')
    if receipt.get('action_admission_eligible') is not False:
        raise RecoveryRejected('admission')
    if receipt.get('app') != 'INKSCAPE':
        raise RecoveryRejected('app')

def app_class_only(receipt, current):
    _common(receipt)
    if receipt.get('app') != current.get('app'):
        raise RecoveryRejected('app_mismatch')
    return {'accepted': True, 'identity_policy': 'app_class_only'}

def surface_bound(receipt, current):
    _common(receipt)
    if receipt.get('app') != current.get('app'):
        raise RecoveryRejected('app_mismatch')
    if type(receipt.get('client_id')) is not int or type(current.get('client_id')) is not int:
        raise RecoveryRejected('surface_missing')
    if receipt['client_id'] != current['client_id']:
        raise RecoveryRejected('surface_mismatch')
    if receipt.get('transient_for') != current.get('transient_for'):
        raise RecoveryRejected('transient_mismatch')
    return {'accepted': True, 'identity_policy': 'surface_bound'}
