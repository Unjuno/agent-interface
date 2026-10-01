"""Connect the existing bounded graph to one caller-owned guarded X11 bridge.

Perception and effect verification are explicit trusted read-only callbacks.
No model, sensor, remint, retry, window handoff or task oracle is supplied here.
"""
import copy
import time
import uuid
from runtime.core_v1.compiled_gui import run as run_graph, validate


def surface(bridge):
    return 'x11-window-' + str(bridge.backend.targets[bridge.target].id)


class _Adapter:
    def __init__(self, bridge, interface, bindings, perceive, verify_effect, cancelled):
        self.interface = validate(interface)
        if self.interface['session_scope'] != bridge.scope or self.interface['surface'] != surface(bridge):
            raise ValueError('interface must name this bridge scope and X11 surface')
        if not all(callable(fn) for fn in (perceive, verify_effect, cancelled)):
            raise ValueError('explicit perception, effect verifier and cancellation callbacks required')
        if type(bindings) is not dict or set(bindings) != set(self.interface['actions']):
            raise ValueError('one exact binding per declared action required')
        self.bindings = copy.deepcopy(bindings)
        for binding in self.bindings.values():
            if type(binding) is not dict or set(binding) != {'interaction','offset','tail'}:
                raise ValueError('exact interaction/offset/tail binding required')
            if binding['interaction'] not in ('click','move','keyboard'):
                raise ValueError('guarded click/move/keyboard interaction required')
            offset = binding['offset']
            if type(offset) is not list or len(offset) != 2 or any(type(v) is not int or v < 0 for v in offset):
                raise ValueError('nonnegative integer reference offset required')
            if type(binding['tail']) is not list:
                raise ValueError('explicit guarded tail list required')
        self.bridge = bridge
        self.scope, self.revision, self.surface = bridge.scope, bridge.binding_revision, surface(bridge)
        self.perceive, self.verifier, self.cancelled = perceive, verify_effect, cancelled
        self.run_id = 'compiled-' + uuid.uuid4().hex
        self.event_index = 0
        self.latest = self.native = self.image = None
        self.authorizations = {}

    def retain(self, kind, value):
        self.event_index += 1
        name = self.run_id + '-' + str(self.event_index) + '-' + kind
        self.bridge._save(name + '.json', copy.deepcopy(value))
        return name

    def associated(self):
        return (self.bridge.scope == self.scope and self.bridge.binding_revision == self.revision
                and surface(self.bridge) == self.surface and not self.bridge.review_required)

    def observe(self, request):
        # Every graph iteration captures through the ordinary retained bridge.
        native = self.bridge.observe()
        _, image = self.bridge.history[native['sequence']]
        self.native, self.image = copy.deepcopy(native), image.copy()
        associated = (self.associated() and native['pointer_binding']['surface'] ==
                      self.bridge.backend.targets[self.bridge.target].id and
                      native['binding_revision'] == self.revision)
        predicates = self.perceive(copy.deepcopy(native), image.copy()) if associated else {}
        if type(predicates) is not dict:
            raise ValueError('perception must return declared predicate values')
        associated = associated and self.associated() and self.bridge.sequence == native['sequence']
        if not associated:
            predicates = {}
        self.latest = {'sequence':native['sequence'],'captured_ns':native['capture_ns'],
            'surface':self.surface if associated else 'association_changed',
            'predicates':copy.deepcopy(predicates),'evidence_ref':'observation-' + str(native['sequence']),
            'evidence_digest':native['native']['artifact']['sha256']}
        self.retain('observation', {'request':request,'observation':self.latest})
        return copy.deepcopy(self.latest)

    def admit(self, request):
        outcome = {'eligible':False,'status':'authority_unavailable','authorization':None,
                   'expected_sequence':request['observation']['sequence'],'valid_until_ns':0}
        action = self.interface['actions'].get(request['action'])
        if (not self.associated() or request['session_scope'] != self.scope or
                request['interface_id'] != self.interface['interface_id']):
            outcome['status'] = 'association_changed'
        elif (action is None or request['operation'] != action['operation'] or
                request['symbol'] != self.interface['symbols'][action['target_symbol']]):
            outcome['status'] = 'missing'
        elif self.latest is None or request['observation'] != self.latest or self.bridge.sequence != self.latest['sequence']:
            outcome['status'] = 'stale'
        elif self.bridge.active is not None or self.bridge.session.recovery_required or not self.bridge._focus_within_target():
            pass
        else:
            symbol = request['symbol']
            predicates = self.latest['predicates']
            # This opt-in adapter uses boolean presence/dependency predicates.
            # A branch alone cannot override absent/unknown target identity.
            needed = [symbol['identity_predicate'], *symbol['dependencies']]
            if any(predicates.get(name) is not True for name in needed):
                outcome['status'] = 'missing'
            else:
                binding = self.bindings[request['action']]
                resolution = self.bridge.store.resolve_point(symbol['target_reference'], binding['offset'],
                    self.native, self.image, time.monotonic_ns(), session_scope=self.scope)
                self.retain('reference', {'action':request['action'],'resolution':resolution})
                if resolution['eligible'] and resolution.get('valid_until_ns',0) > time.monotonic_ns():
                    authorization = uuid.uuid4().hex
                    deadline = min(resolution['valid_until_ns'],time.monotonic_ns()+5_000_000_000)
                    outcome.update(eligible=True,status='revalidated',authorization=authorization,valid_until_ns=deadline)
                    self.authorizations[authorization] = {'action':request['action'],'operation':request['operation'],
                        'expected_sequence':self.latest['sequence'],'valid_until_ns':deadline,
                        'target_reference':symbol['target_reference']}
                else:
                    outcome['status'] = {'STALE':'stale','MISSING':'missing','SCOPE_MISMATCH':'association_changed'}.get(resolution['status'],'authority_unavailable')
        self.retain('admission', {'request':request,'result':outcome})
        return outcome

    def execute(self, request):
        # Consume before checking or dispatching; an uncertain return cannot replay.
        authorization = self.authorizations.pop(request['authorization'],None)
        action_id = 'action-' + uuid.uuid4().hex
        rejected = (authorization is None or not self.associated() or
            self.bridge.sequence != request['expected_sequence'] or
            type(request['valid_until_ns']) is not int or request['valid_until_ns'] <= time.monotonic_ns())
        if authorization is not None:
            rejected = rejected or any(request[k] != authorization[k] for k in ('action','operation','expected_sequence'))
            rejected = rejected or request['valid_until_ns'] > authorization['valid_until_ns']
        if rejected:
            raw = {'status':'refused','error':'COMPILED_AUTHORIZATION_INVALID','input_dispatched':False}
        else:
            binding = self.bindings[request['action']]
            raw = getattr(self.bridge,binding['interaction'])(authorization['target_reference'],binding['offset'],
                tail=copy.deepcopy(binding['tail']), expires_at_ns=request['valid_until_ns'])
        effect_ref = self.retain('execution', {'request':request,'action_id':action_id,'result':raw})
        releases = raw.get('execution',{}).get('releases',[])
        neutral = (bool(releases) and not raw.get('recovery_required',False) and
                   all(r.get('verified') is True and r.get('keys_down') == [] and
                       r.get('buttons_down') == [] for r in releases))
        # A refusal with no actual release receipt does not invent neutrality.
        terminal = {'status':raw['status'],'action_id':action_id,'effect_ref':effect_ref,
                    'release':{'verified':neutral,'keys_down':[],'buttons_down':[]}}
        self.retain('terminal',terminal)
        return terminal

    def verify_effect(self, request):
        if (not self.associated() or self.latest != request['observation'] or
                self.bridge.sequence != self.latest['sequence']):
            result = {'status':'unavailable','evidence_ref':request['observation']['evidence_ref']}
        else:
            result = self.verifier(copy.deepcopy(request),copy.deepcopy(self.native),self.image.copy())
            if not self.associated() or self.bridge.sequence != self.latest['sequence']:
                result = {'status':'unavailable','evidence_ref':request['observation']['evidence_ref']}
        self.retain('effect', {'request':request,'result':result})
        return result

    def execute_method(self):
        self.retain('plan', {'interface':self.interface,'bindings':self.bindings,
            'scope':'trusted caller-owned read-only perception/effect callbacks; not independent task scoring'})
        try:
            result = run_graph(self.interface, {'observe':self.observe,'admit':self.admit,
                'execute':self.execute,'verify_effect':self.verify_effect,'cancelled':self.cancelled,
                'journal':lambda event:self.retain('event',event)}, clock=time.monotonic_ns)
        except Exception as error:
            self.retain('exception', {'error':repr(error),'replay_allowed':False,
                'effect_status':'unknown; inspect retained bridge receipts before any new action'})
            raise
        finally:
            self.authorizations.clear()
        self.retain('receipt',result)
        return result


def run(bridge, interface, bindings, *, perceive, verify_effect, cancelled=lambda:False):
    """Run the existing graph once against freshly grounded bridge aliases.

    Symbols name existing aliases; bindings specify each guarded interaction,
    offset and tail. Callbacks receive copies of this capture and its exact RGB.
    Boolean symbol dependencies must all be True. Callbacks are trusted caller
    code, not sandboxed or independently certified. Changed pixels do not verify
    text or durable effects. Caller must independently score the task afterward.
    Raw captures, resolutions, input receipts and graph events are retained in
    the bridge output directory. No automatic replay/repair or scope renewal.
    """
    return _Adapter(bridge,interface,bindings,perceive,verify_effect,cancelled).execute_method()
