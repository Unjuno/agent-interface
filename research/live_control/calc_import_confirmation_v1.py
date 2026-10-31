"""One guarded dialog-confirmation attempt after a retained Calc paste yield.

Caller owns and closes both sessions, supplies reviewed target/preview evidence,
and must independently observe the import effect before any subsequent Save.
The supplied prior receipt/session binding is trusted caller custody, not a
cryptographic proof of provenance. This module never replays the prior entry.
"""
import copy
import re
from research.live_control.reviewed_preview_gate_v1 import ReviewedPreviewGate


def _neutral(release):
    return (type(release) is dict and release.get('verified') is True and
            release.get('keys_down') == [] and release.get('buttons_down') == [])


def _prior_ok(receipt, closed, scope, session_id):
    if (type(receipt) is not dict or type(closed) is not dict or
            type(scope) is not str or not scope or type(session_id) is not str or not session_id or
            receipt.get('format') != 'compiled-gui-runtime-receipt-v1' or
            receipt.get('session_scope') != scope or receipt.get('outcome') != 'SAFE_YIELD' or
            receipt.get('reason') != 'effect_unavailable' or
            type(receipt.get('completed_transitions')) is not int or receipt['completed_transitions'] != 1 or
            closed.get('status') != 'closed' or closed.get('session_id') != session_id or
            closed.get('authority_granted') is not False or closed.get('restart_allowed') is not False or
            closed.get('release_attempted') is not True or not _neutral(closed.get('release'))):
        return False
    pending, transitions = receipt.get('pending_effect'), receipt.get('transitions')
    if type(pending) is not dict or type(transitions) is not list or len(transitions) != 1:
        return False
    effect = pending.get('expected_effect')
    transition = transitions[0]
    return (pending.get('action') == 'enter' and type(effect) is dict and set(effect) == {'cells_match'} and
            effect['cells_match'] is True and type(pending.get('effect_ref')) is str and bool(pending['effect_ref']) and
            type(transition) is dict and transition.get('action') == 'enter' and
            transition.get('effect_ref') == pending['effect_ref'] and transition.get('release_verified') is True)


class ImportConfirmation:
    def __init__(self, owner, gate, *, prior_receipt, prior_close, prior_scope,
                 prior_session_id, alias, point, region_size):
        if not _prior_ok(prior_receipt, prior_close, prior_scope, prior_session_id):
            raise ValueError('retained prior yield and neutral closed session required')
        if (type(gate) is not ReviewedPreviewGate or getattr(owner, 'bridge', None) is not gate.bridge or
                getattr(owner, 'state', None) != 'open' or getattr(owner, 'session_id', None) == prior_session_id or
                type(getattr(owner, 'session_id', None)) is not str or not owner.session_id or
                getattr(owner, 'dispatch_attempted', None) is not False or gate.used or
                type(alias) is not str or re.fullmatch(r'[a-z][a-z0-9_]{0,31}', alias) is None or
                type(point) is not list or len(point) != 2 or any(type(x) is not int for x in point) or
                type(region_size) is not tuple or len(region_size) != 2 or
                any(type(x) is not int or x <= 0 for x in region_size)):
            raise ValueError('fresh modal owner, gate and reviewed target required')
        self.owner, self.gate = owner, gate
        self.bridge, self.session_id = gate.bridge, owner.session_id
        self.alias, self.point, self.region_size = alias, point.copy(), region_size
        self.used = False

    def _owner_current(self):
        return (getattr(self.owner, "bridge", None) is self.bridge and
                getattr(self.owner, "session_id", None) == self.session_id and
                getattr(self.owner, "state", None) == "open" and
                getattr(self.owner, "dispatch_attempted", None) is False)

    def run(self, native, image):
        if self.used:
            raise ValueError('confirmation attempt is single use')
        self.used = True
        result = {'status': 'unavailable', 'entry_replayed': False, 'import_effect': 'unverified'}
        try:
            if not self._owner_current():
                return result
            geometry = native['pointer_binding']['geometry']
            if (type(geometry) is not list or len(geometry) != 4 or any(type(x) is not int for x in geometry) or
                    geometry[2] <= 0 or geometry[3] <= 0):
                return result
            x, y = self.point
            width, height = self.region_size
            left, top = x - width // 2, y - height // 2
            if not (geometry[0] <= left and geometry[1] <= top and
                    left + width <= geometry[0] + geometry[2] and top + height <= geometry[1] + geometry[3] and
                    0 <= left and 0 <= top and left + width <= image.width and top + height <= image.height):
                result['status'] = 'rejected'
                return result
            gate_result = self.gate.arm(native, image)
            result['preview'] = copy.deepcopy(gate_result)
            if gate_result.get('status') != 'armed' or self.gate.guard is None:
                result['status'] = 'rejected' if gate_result.get('status') == 'wrong' else 'unavailable'
                return result
            guard = self.gate.guard
            if not self._owner_current():
                return result
            now = self.gate.clock()
            if type(now) is not int or now >= self.gate.deadline_ns:
                return result
            # A failed mint can consume an alias; this attempt is never retried.
            result['mint_may_be_consumed'] = True
            reference = self.owner.bridge.mint_reference(self.alias, native['sequence'], self.point,
                                                         region_size=self.region_size)
            offset = reference['offset']
            now = self.gate.clock()
            if not self._owner_current() or type(now) is not int or now >= self.gate.deadline_ns:
                return result
            self.owner.dispatch_attempted = True
            with self.owner.bridge.input_guard(self.alias, offset, tail=[],
                                               verify=lambda stage, obs, rgb: guard.verify_capture(obs, rgb),
                                               interaction='click'):
                action = self.owner.bridge.click(self.alias, offset, tail=[], expires_at_ns=self.gate.deadline_ns)
            result['action'] = copy.deepcopy(action)
            if type(action) is dict and action.get('status') == 'refused' and action.get('input_dispatched') is False:
                result['status'] = 'refused'
            elif type(action) is dict and action.get('status') == 'completed' and action.get('recovery_required') is False:
                execution = action.get('execution')
                releases = execution.get('releases') if type(execution) is dict else None
                if type(releases) is list and releases and all(_neutral(row) for row in releases):
                    result['status'] = 'input_completed'
                else:
                    result['status'] = 'uncertain'
            else:
                result['status'] = 'uncertain'
        except Exception as error:
            result['error_type'] = type(error).__name__
            if getattr(self.owner, 'dispatch_attempted', None) is not False:
                result['status'] = 'uncertain'
        return result
