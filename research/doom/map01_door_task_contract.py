"""Finite command-shape and evidence guard for a MAP01 door experiment.

This class does not read the input owner or grant authority on its own. The
caller must independently obtain a fresh owner/focus/process snapshot and
apply the returned deadline to the executor before submitting an operation.
"""
def _release_matches(identifier, identity, terminal, accepted, *, allow_no_token=False):
    if type(terminal) is not dict or type(accepted) is not dict:
        return False
    token=accepted.get('intent_token')
    release=terminal.get('release')
    return (accepted.get('id')==identifier and type(token) is str and bool(token)
            and terminal.get('id')==identifier and terminal.get('status')=='completed'
            and terminal.get('input_owner_id')==identity[0]
            and terminal.get('input_owner_generation')==identity[1]
            and type(release) is dict and release.get('event')=='owner_release'
            and (release.get('intent_token')==token or allow_no_token and release.get('intent_token') is None)
            and release.get('verified') is True
            and all(release.get(k)==[] for k in ('keys_down','buttons_down','keys_unknown','key_state_errors')))


import hashlib
import json
import math
from doom_controller_failure_cleanup_v1 import operation_release_verified, owner_event_verified


class DoorTaskContract:
    def __init__(self, arm):
        if arm not in ('control','use'):
            raise ValueError('invalid arm')
        self.arm=arm
        self.index=0
        self.inflight=None
        self.identity=None
        self.last_sequence=0

    @property
    def finished(self):
        return self.index==5 and self.inflight is None

    def authorize(self, command, source, now, terminal, accepted):
        if self.inflight is not None or self.finished or type(command) is not dict or type(source) is not dict:
            raise ValueError('unexpected submission')
        identifier='approach-'+str(self.index+1) if self.index<4 else 'intervention'
        if self.index<4:
            steps=[{'op':'hold','keys':['Up'],'duration_ms':600}]
        elif self.arm=='use':
            steps=[{'op':'hold','keys':['e'],'duration_ms':120}]
        else:
            steps=[{'op':'coast','duration_ms':120,'sample_ms':100}]
        seq=source.get('sequence');capture=source.get('capture_ns')
        owner=source.get('renewal_owner_id');generation=source.get('input_owner_generation')
        pointer=source.get('pointer_binding');process=source.get('target_process_identity')
        window=source.get('target_renewal_window_identity')
        valid=command.get('valid_until_ns')
        if (command.get('op')!='submit' or command.get('id')!=identifier or command.get('steps')!=steps
            or type(seq) is not int or seq<=self.last_sequence or command.get('expected_sequence')!=seq
            or type(capture) is not int or type(now) is not int or not 0<=now-capture<2_000_000_000
            or type(valid) is not int or not now<valid<=now+30_000_000_000
            or type(owner) is not str or not owner or type(generation) is not int or generation<0
            or source.get('id')!=('approach-'+str(self.index) if self.index else 'cover-0')
            or source.get('exact') is not True or source.get('focus_samples_match') is not True
            or type(pointer) is not dict or type(pointer.get('focus')) is not int
            or pointer.get('focus')!=pointer.get('surface')
            or source.get('input_focus_before')!=pointer['focus'] or source.get('input_focus_after')!=pointer['focus']
            or type(process) is not dict or process.get('sequence')!=seq
            or process.get('surface')!=pointer['surface']
            or type(process.get('digest')) is not str or not process['digest']
            or type(window) is not dict or window.get('sequence')!=seq
            or window.get('surface')!=pointer['surface'] or type(window.get('digest')) is not str or not window['digest']):
            raise ValueError('invalid source or command')
        identity=(owner,generation,pointer['surface'],process['digest'],window['digest'])
        if self.identity is not None and identity!=self.identity:
            raise ValueError('input target changed')
        prior='approach-'+str(self.index) if self.index else 'cover-0'
        if not _release_matches(prior,identity,terminal,accepted,allow_no_token=self.index==0):
            raise ValueError('previous release unavailable')
        self.identity=identity
        self.last_sequence=seq
        self.inflight=identifier
        self.steps=steps
        self.sequence=seq
        self.valid_until=valid
        self.deadline=min(now+1_000_000_000,capture+2_000_000_000,valid)
        return self.deadline

    def authorize_live(self, command, source, started, terminal, accepted, gate, backend):
        # _owner_and_source performs the runtime's live process, focus, owner,
        # neutral input and latest-source checks. It must run on every submit.
        owner,generation,snapshot,engine=gate._owner_and_source(backend,source,command,started)
        now=gate.clock()
        projected=gate._clock_reserve_deadline(engine,started)
        reserve=gate.clock_reserve_deadline_ns
        if (owner!=source.get('renewal_owner_id') or generation!=source.get('input_owner_generation')
                or type(snapshot) is not dict or type(snapshot.get('sample_started_ns')) is not int
                or type(snapshot.get('sample_finished_ns')) is not int
                or not started<=snapshot['sample_started_ns']<=snapshot['sample_finished_ns']<=now
                or type(projected) is not int or type(reserve) is not int
                or type(now) is not int or now>=min(started+1_000_000_000,projected,reserve)):
            raise ValueError('live owner or clock gate expired')
        deadline=self.authorize(command,source,started,terminal,accepted)
        self.deadline=min(deadline,projected,reserve)
        if now>=self.deadline:
            # Consume the sequence on uncertainty; do not allow a retry.
            raise ValueError('input deadline expired')
        return self.deadline

    def submit_live(self, command, source, started, terminal, accepted, gate, backend, executor):
        if getattr(executor,'active',None) is not None:
            raise ValueError('executor is not idle')
        deadline=self.authorize_live(command,source,started,terminal,accepted,gate,backend)
        # A raised submit leaves inflight set: the caller must stop rather
        # than risk replaying an operation whose dispatch status is unknown.
        executor.submit(command['id'],command['steps'],command['expected_sequence'],
                        command['valid_until_ns'],admission_deadline_ns=deadline)
        return deadline

    def completed(self, identifier, terminal, accepted, events):
        if (self.inflight is None or type(identifier) is not str or not identifier
                or self.inflight!=identifier or not _release_matches(identifier,self.identity,terminal,accepted,
                    allow_no_token=self.steps[0]['op']=='coast')
                or type(events) is not list or not operation_release_verified(identifier,events,
                    require_intent=self.steps[0]['op']=='hold')):
            raise ValueError('operation completion or release unavailable')
        program=hashlib.sha256(json.dumps(self.steps,sort_keys=True,separators=(',',':'),
                                         ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        rows=[r for r in events if type(r) is dict and r.get('id')==identifier]
        observed_accepted=[r for r in rows if r.get('event')=='accepted']
        observed_terminals=[r for r in rows if r.get('event')=='terminal']
        downs=[r for r in rows if r.get('event')=='input_admission']
        ups=[r for r in rows if r.get('event')=='input_release_transition']
        strip_emit=lambda row:{k:v for k,v in row.items() if k!='emit_ns'}
        if (len(observed_accepted)!=1 or strip_emit(observed_accepted[0])!=strip_emit(accepted)
                or len(observed_terminals)!=1 or strip_emit(observed_terminals[0])!=strip_emit(terminal)
                or type(accepted.get('steps')) is not int or accepted['steps']!=len(self.steps)
                or accepted.get('program_sha256')!=program
                or terminal.get('steps_completed')!=len(self.steps)
                or any(r.get('event')=='pointer_admission' for r in rows)):
            raise ValueError('operation event stream differs')
        keyed=self.steps[0]['op']=='hold'
        if not keyed:
            started=[r for r in rows if r.get('event')=='step_started']
            coast=[r for r in rows if r.get('event')=='coast_result']
            completed=[r for r in rows if r.get('event')=='step_completed']
            typed=[r for r in rows if r.get('event')=='typed_observation']
            frames=[r for r in rows if r.get('event')=='observation']
            if (downs or ups or len(started)!=1 or len(coast)!=1 or len(completed)!=1 or not typed
                    or len(typed)!=len(frames) or started[0].get('step')!=0
                    or started[0].get('operation')!='coast' or coast[0].get('step')!=0
                    or coast[0].get('input_admissions')!=0
                    or type(coast[0].get('samples')) is not int or coast[0]['samples']!=len(frames)
                    or type(coast[0].get('elapsed_ms')) not in (int,float)
                    or not math.isfinite(coast[0]['elapsed_ms'])
                    or coast[0]['elapsed_ms']<self.steps[0]['duration_ms']
                    or completed[0].get('step')!=0 or type(started[0].get('issued_ns')) is not int
                    or type(completed[0].get('completed_ns')) is not int
                    or type(terminal.get('terminal_ns')) is not int
                    or not started[0]['issued_ns']<=completed[0]['completed_ns']<=terminal['terminal_ns']
                    or not rows.index(started[0])<rows.index(coast[0])<rows.index(completed[0])
                    or any(r.get('event')=='keys_held' or r.get('keys_held',[])!=[] for r in rows)
                    or any(a.get('step')!=0 or b.get('step')!=0
                           or any(a.get(k)!=b.get(k) for k in ('id','sequence','capture_ns','frame_rgb_sha256'))
                           or type(a.get('capture_ns')) is not int
                           or not started[0]['issued_ns']<=a['capture_ns']<=completed[0]['completed_ns']
                           or not rows.index(a)<rows.index(b)<rows.index(coast[0])
                           for a,b in zip(typed,frames))):
                raise ValueError('passive observation or release differs')
        else:
            if len(downs)!=1 or len(ups)!=1:
                raise ValueError('key admission or release missing')
            down,transition=downs[0],ups[0]
            up=transition.get('owner_thread_keyup_receipt')
            token=accepted['intent_token'];key=self.steps[0]['keys'][0]
            held=[r for r in rows if r.get('event')=='keys_held' and r.get('step')==0]
            step_done=[r for r in rows if r.get('event')=='step_completed' and r.get('step')==0]
            typed=[r for r in rows if r.get('event')=='typed_observation' and r.get('step')==0]
            frames=[r for r in rows if r.get('event')=='observation' and r.get('step')==0]
            if (terminal['release'].get('intent_token')!=token
                    or down.get('step')!=0 or down.get('key')!=key
                    or down.get('owner_id')!=self.identity[0] or down.get('intent_token')!=token
                    or down.get('valid_until_ns')!=self.valid_until
                    or down.get('target_process_identity')!=[self.sequence,self.identity[2],self.identity[3],self.valid_until]
                    or type(accepted.get('accepted_ns')) is not int
                    or type(down.get('admitted_ns')) is not int or type(down.get('input_ack_ns')) is not int
                    or type(down.get('first_press_deadline_ns')) is not int
                    or not 0<down['first_press_deadline_ns']<=self.deadline
                    or not accepted['accepted_ns']<=down['admitted_ns']<=down['input_ack_ns']<down['first_press_deadline_ns']
                    or down.get('first_press_submission_checked_before_deadline') is not True
                    or not rows.index(observed_accepted[0])<rows.index(down)<rows.index(transition)<rows.index(observed_terminals[0])
                    or transition.get('step')!=0 or transition.get('operation')!='up'
                    or transition.get('key')!=key or transition.get('owner_id')!=self.identity[0]
                    or transition.get('intent_token')!=token or transition.get('owner_transition_verified') is not True
                    or transition.get('admission_receipt_valid') is not True
                    or transition.get('admission_receipt')!=dict({k:v for k,v in down.items() if k!='emit_ns'},operation='down')
                    or type(up) is not dict or up.get('event')!='owner_explicit_keyup'
                    or not owner_event_verified(up) or up.get('owner_id')!=self.identity[0]
                    or len(held)!=1 or held[0].get('keys')!=[key]
                    or type(held[0].get('input_ack_ns')) is not int
                    or not down['input_ack_ns']<=held[0]['input_ack_ns']
                    or up['owner_keyrelease_started_ns']-held[0]['input_ack_ns']<self.steps[0]['duration_ms']*1_000_000
                    or not rows.index(down)<rows.index(held[0])<rows.index(transition)
                    or len(step_done)!=1 or type(step_done[0].get('completed_ns')) is not int
                    or not typed or len(typed)!=len(frames)
                    or any(any(a.get(k)!=b.get(k) for k in ('id','sequence','capture_ns','frame_rgb_sha256'))
                           for a,b in zip(typed,frames))
                    or type(frames[-1].get('capture_ns')) is not int
                    or not up['owner_keymap_sampled_ns']<=frames[-1]['capture_ns']<=step_done[0]['completed_ns']
                    or not rows.index(transition)<rows.index(typed[-1])<rows.index(frames[-1])<rows.index(step_done[0])
                    or step_done[0]['completed_ns']>terminal['terminal_ns']
                    or up.get('release_batch_key_order')!=[key] or up.get('valid_until_ns')!=self.valid_until
                    or up.get('intent_token')!=token or up.get('key')!=key
                    or up.get('keycode')!=down.get('keycode')
                    or up.get('owner_keyrelease_started_ns',0)<down['input_ack_ns']
                    or type(terminal['release'].get('verified_ns')) is not int
                    or type(terminal.get('terminal_ns')) is not int
                    or not up['owner_keymap_sampled_ns']<=terminal['release']['verified_ns']<=terminal['terminal_ns']):
                raise ValueError('key admission or release evidence differs')
        self.inflight=None
        self.index+=1


def validate_initial_cover(source, terminal, accepted, events):
    # Validate one preregistered passive cover without granting input.
    if type(source) is not dict or source.get('id')!='initial':
        raise ValueError('cover source unavailable')
    owner=source.get('renewal_owner_id');generation=source.get('input_owner_generation')
    binding=source.get('pointer_binding');process=source.get('target_process_identity')
    window=source.get('target_renewal_window_identity');seq=source.get('sequence')
    if (type(owner) is not str or not owner or type(generation) is not int or generation<0
            or type(seq) is not int or seq<1 or source.get('exact') is not True
            or source.get('focus_samples_match') is not True or type(binding) is not dict
            or type(binding.get('focus')) is not int or binding['focus']!=binding.get('surface')
            or source.get('input_focus_before')!=binding['focus'] or source.get('input_focus_after')!=binding['focus']
            or type(process) is not dict or process.get('sequence')!=seq or process.get('surface')!=binding['surface']
            or type(process.get('digest')) is not str or not process['digest']
            or type(window) is not dict or window.get('sequence')!=seq or window.get('surface')!=binding['surface']
            or type(window.get('digest')) is not str or not window['digest']):
        raise ValueError('cover source identity differs')
    checker=DoorTaskContract('control')
    checker.identity=(owner,generation,binding['surface'],process['digest'],window['digest'])
    checker.inflight='cover-0'
    checker.steps=[{'op':'coast','duration_ms':200,'sample_ms':100}]
    checker.completed('cover-0',terminal,accepted,events)
