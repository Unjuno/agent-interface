"""G10-shaped explicit second-target proposal on the shared guarded adapter.

The trusted provider supplies a new proposal from a copied current observation;
no target is inferred from the old coordinate. This does not issue authority.
"""
import copy
import time
from runtime.guarded_x11_v1.compiled import _Adapter
from research.live_control.calc_fresh_reference_v1 import mint_from_proposal


class _FreshSecondAdapter(_Adapter):
    def __init__(self, bridge, interface, bindings, perceive, verify_effect,
                 cancelled, proposal_provider):
        super().__init__(bridge, interface, bindings, perceive, verify_effect, cancelled)
        if not callable(proposal_provider):
            raise ValueError('explicit proposal provider required')
        actions = self.interface['actions']
        if set(actions) != {'first', 'second'}:
            raise ValueError('G10 first/second actions required')
        self.first_ref = self.interface['symbols'][actions['first']['target_symbol']]['target_reference']
        self.second_ref = self.interface['symbols'][actions['second']['target_symbol']]['target_reference']
        if self.first_ref == self.second_ref:
            raise ValueError('distinct first and second references required')
        self.proposal_provider = proposal_provider
        self.first_returned_ns = None
        self.second_attempted = False

    def execute(self, request):
        terminal = super().execute(request)
        if (request['action'] == 'first' and terminal['status'] == 'completed' and
                terminal['release']['verified'] is True and
                terminal['release']['keys_down'] == [] and terminal['release']['buttons_down'] == []):
            self.first_returned_ns = time.monotonic_ns()
        return terminal

    def admit(self, request):
        if request['action'] != 'second':
            return super().admit(request)
        denied = {'eligible': False, 'status': 'missing', 'authorization': None,
                  'expected_sequence': request['observation']['sequence'], 'valid_until_ns': 0}
        action = self.interface['actions']['second']
        symbol = self.interface['symbols'][action['target_symbol']]
        if (self.second_attempted or self.first_returned_ns is None or self.latest is None or
                request.get('interface_id') != self.interface['interface_id'] or
                request.get('session_scope') != self.scope or
                request.get('operation') != action['operation'] or request.get('symbol') != symbol or
                request['observation'] != self.latest or not self.associated() or
                self.bridge.sequence != self.latest['sequence'] or self.bridge.active is not None or
                self.bridge.session.recovery_required or not self.bridge._focus_within_target() or
                any(self.latest['predicates'].get(name) is not True
                    for name in [symbol['identity_predicate'], *symbol['dependencies']])):
            return denied
        self.second_attempted = True
        try:
            if self.cancelled() is not False:
                return denied
            proposal = self.proposal_provider(copy.deepcopy(self.native), self.image.copy())
            if type(proposal) is not dict or proposal.get('alias') != self.second_ref:
                self.retain('fresh-reference', {'status': 'UNAVAILABLE', 'reason': 'proposal_alias'})
                return denied
            if self.cancelled() is not False:
                return denied
            result = mint_from_proposal(self.bridge, proposal, scope=self.scope,
                                        after_ns=self.first_returned_ns)
            self.retain('fresh-reference', result)
            if (result.get('status') != 'REFERENCE_MINTED' or
                    result.get('offset') != self.bindings['second']['offset']):
                return denied
        except Exception as error:
            self.retain('fresh-reference', {'status': 'UNAVAILABLE', 'error_type': type(error).__name__,
                                             'alias_may_be_consumed': True})
            return denied
        # The standard guarded adapter still resolves the alias, issues an
        # expiring private admission and checks dependencies again at input.
        return super().admit(request)


def run_with_fresh_proposal(bridge, interface, bindings, *, perceive, verify_effect,
                            proposal_provider, cancelled=lambda: False):
    return _FreshSecondAdapter(bridge, interface, bindings, perceive, verify_effect,
                               cancelled, proposal_provider).execute_method()

def run_with_bounded_fresh_proposal(bridge, interface, bindings, *, perceive,
                                    verify_effect, proposal_worker, cancelled):
    """Require one fresh bounded worker sharing the graph's cancellation check.

    The caller retains the worker to inspect a possibly still-running callback.
    This bounds only its wait, not Python scheduling, native calls or shutdown.
    """
    from research.live_control.calc_bounded_proposal_v1 import BoundedProposal
    if (type(proposal_worker) is not BoundedProposal or not callable(cancelled) or
            proposal_worker.cancelled is not cancelled):
        raise ValueError('bounded worker with the same cancellation callback required')
    state = proposal_worker.snapshot()
    if state['used'] or state['retired']:
        raise ValueError('fresh proposal worker required')
    return run_with_fresh_proposal(bridge, interface, bindings, perceive=perceive,
                                   verify_effect=verify_effect,
                                   proposal_provider=proposal_worker, cancelled=cancelled)