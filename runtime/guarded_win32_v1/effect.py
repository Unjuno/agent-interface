"""Post-release observation for an explicit trusted caller effect predicate."""
import copy, time, subprocess

def verify(owner, action, execution, callback, deadline):
    result = {'status': 'unknown', 'task_success': None, 'observation': None}
    o = owner.observer

    def pending():
        receipt = getattr(callback, 'receipt', None)
        if isinstance(receipt, dict) and receipt.get('reason') == 'termination_unconfirmed':
            process = receipt.get('process')
            if isinstance(process, subprocess.Popen):
                owner.pending_verifier = process
                result['pending_pid'] = process.pid
            else:
                o.review_required = True
            return True
        return False

    def associated(row=None):
        if not owner.neutral() or owner.session.recovery_required or o.review_required or (owner.cancelled() is not False) or (time.monotonic_ns() >= deadline):
            return False
        if o.scope != action['scope'] or o.binding_revision != action['row']['binding_revision'] or o._binding() != action['row']['pointer_binding']:
            o.review_required = True
            return False
        return row is None or o.sequence == row['sequence']
    try:
        if execution.get('status') != 'completed' or not associated():
            return result
        g = action['row']['pointer_binding']['geometry']
        row = o.observe([0, 0, g['width'], g['height']])
        _, image = o.get(row['sequence'])
        result['observation'] = copy.deepcopy(row)
        if not associated(row):
            return result
        verdict = callback(copy.deepcopy(action['program']), copy.deepcopy(execution), copy.deepcopy(row), image.copy())
        joined = associated(row)
        if pending() or not joined:
            return result
        if verdict is not True and verdict is not False and (verdict is not None):
            raise ValueError('effect predicate must return True, False or None')
        result.update(status='verified' if verdict is True else 'not_verified' if verdict is False else 'unknown', task_success=verdict)
    except Exception as error:
        pending()
        try:
            associated()
        except Exception:
            o.review_required = True
        owner.neutral()
        result['error'] = {'type': type(error).__name__, 'detail': str(error)}
    return result
