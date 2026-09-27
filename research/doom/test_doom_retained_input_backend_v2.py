"""Two-key ordering regression for post-batch release telemetry."""
import importlib.util
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent


class Parent:
    pass
parent_mod = types.ModuleType('doom_typed_coast_backend_v1'); parent_mod.Backend = Parent; parent_mod.suite = object()
sys.modules['doom_typed_coast_backend_v1'] = parent_mod
owner_mod = types.ModuleType('input_transition_owner_v2'); owner_mod.InputOwner = object
sys.modules['input_transition_owner_v2'] = owner_mod
spec = importlib.util.spec_from_file_location('doom_retained_input_backend_v2', HERE / 'doom_retained_input_backend_v2.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


class Lease:
    intent_token = 'intent-1'
    def __init__(self, interruption=None): self._interruption = interruption
    def interruption_snapshot(self): return self._interruption


class Owner:
    def __init__(self, state=None):
        self.calls = []
        self.clock = 100
        self.state = state or {'owner_id':'owner-1','sample_started_ns':500,'sample_finished_ns':510,'owned_keycodes':[]}
    def call(self, op, lease=None, key=None):
        self.calls.append((op, key))
        if op == 'up':
            self.clock += 10
            return {'event':'input_release_receipt_v2','operation':'up','key':key,
                    'owner_id':'owner-1','intent_token':getattr(lease,'intent_token',None),
                    'release_call_started_ns':self.clock,'release_call_returned_ns':self.clock+5,
                    'grants_input_authority':False}
        if op == 'down':
            return {'event':'input_admission','key':key,'intent_token':getattr(lease,'intent_token',None)}
        if op == 'input_state': return dict(self.state)
        raise AssertionError(op)


def make(held, interruption=None, state=None):
    obj = object.__new__(mod.Backend)
    obj.owner = Owner(state); obj.lease = Lease(interruption); obj.held = set(held); obj._release_receipts = []
    emitted=[]; obj.emit=emitted.append
    return obj, emitted


def test_two_key_sample_and_emit_only_after_both_up_calls():
    obj, emitted = make({'a','d'})
    obj.raw('a', False)
    assert obj.owner.calls == [('up','a')]
    assert emitted == []
    obj.raw('d', False)
    assert obj.owner.calls == [('up','a'),('up','d'),('input_state',None)]
    assert len(emitted) == 1
    row=emitted[0]
    assert row['event']=='input_release_batch_v2'
    assert row['keys']==['a','d']
    assert len(row['receipts'])==2
    assert row['owner_transition_verified'] is True


def test_single_key_one_sample_one_publication():
    obj, emitted = make({'a'})
    obj.raw('a', False)
    assert obj.owner.calls == [('up','a'),('input_state',None)]
    assert len(emitted)==1 and emitted[0]['owner_transition_verified'] is True


def test_owner_not_empty_fails_closed():
    state={'owner_id':'owner-1','sample_started_ns':500,'sample_finished_ns':510,'owned_keycodes':[38]}
    obj, emitted = make({'a'}, state=state); obj.raw('a',False)
    assert emitted[0]['owner_transition_verified'] is False


def test_interruption_fails_direct_attribution():
    interruption={'record':{'event':'owner_release','reason':'cancelled','verified_ns':90}}
    obj, emitted = make({'a'}, interruption=interruption); obj.raw('a',False)
    assert emitted[0]['owner_transition_verified'] is False
    assert emitted[0]['interruption_reason']=='cancelled'


def test_stale_backend_ownership_fails_closed():
    obj, emitted = make(set()); obj.raw('a',False)
    assert emitted[0]['receipts'][0]['backend_owned_before_release'] is False
    assert emitted[0]['owner_transition_verified'] is False


def test_down_emits_immediately_without_state_sample():
    obj, emitted = make(set()); obj.raw('a',True)
    assert obj.owner.calls == [('down','a')]
    assert obj.held == {'a'} and emitted[0]['event']=='input_admission'


def main():
    tests=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for test in tests:test()
    print(f'PASS doom retained-input backend v2 {len(tests)}/{len(tests)}')


if __name__=='__main__':main()
