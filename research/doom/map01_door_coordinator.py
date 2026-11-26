"""Coordinator for the finite MAP01 door experiment.

The caller must register this receiver in a dedicated opt-in session, and
must route all executor events to record(). No normal task access is granted.
"""
from copy import deepcopy
from map01_door_journal import DoorEventJournal
from map01_door_task_contract import DoorTaskContract, validate_initial_cover


class _CoverValidator:
    def __init__(self, source):
        self.source=deepcopy(source)

    def completed(self, identifier, terminal, accepted, events):
        if identifier!='cover-0':
            raise ValueError('unexpected cover identifier')
        validate_initial_cover(self.source,terminal,accepted,events)


class DoorCoordinator:
    def __init__(self, arm, gate, backend, executor, clock):
        self.contract=DoorTaskContract(arm)
        self.journal=DoorEventJournal()
        self.gate=gate
        self.backend=backend
        self.executor=executor
        self.clock=clock
        self.cover_done=False
        self.pending=None
        self.last_completed=None
        self._cover_source=None

    @property
    def finished(self):
        return (self.cover_done and self.pending is None and self.journal.ready
                and self.contract.finished)

    def record(self, event):
        self.journal.record(event)

    def submit_cover(self, command, source):
        if self.pending is not None or self.cover_done or not self.journal.ready:
            raise ValueError('cover already attempted')
        now=self.clock()
        if (type(command) is not dict or command.get('op')!='submit' or command.get('id')!='cover-0'
                or command.get('steps')!=[{'op':'coast','duration_ms':200,'sample_ms':100}]
                or type(source) is not dict or source.get('id')!='initial'
                or type(source.get('sequence')) is not int or command.get('expected_sequence')!=source['sequence']
                or type(now) is not int or type(command.get('valid_until_ns')) is not int
                or not now<command['valid_until_ns']<=now+30_000_000_000
                or self.executor.active is not None):
            raise ValueError('invalid initial cover')
        self._cover_source=deepcopy(source)
        try:
            deadline=self.gate.check_submit(command,self.backend,source,terminal=None,accepted=None)
            if type(deadline) is not int:
                raise ValueError('invalid cover deadline')
            deadline=min(deadline,command['valid_until_ns'])
            if self.clock()>=deadline:
                raise ValueError('cover deadline expired')
            self.journal.begin('cover-0',min(command['valid_until_ns'],now+5_000_000_000))
            self.pending='cover-0'
            self.executor.submit('cover-0',command['steps'],command['expected_sequence'],
                                 command['valid_until_ns'],admission_deadline_ns=deadline)
        except Exception:
            self.journal.fail('initial cover dispatch failed')
            raise

    def submit_next(self, command, source):
        if (not self.cover_done or self.pending is not None or not self.journal.ready
                or self.last_completed is None or self.executor.active is not None):
            raise ValueError('prior operation has not settled')
        accepted,terminal=self.journal.completion(self.last_completed)
        observed=self.journal.latest_observation(self.last_completed)
        clean=lambda row:{k:v for k,v in row.items() if k not in ('emit_ns','stdout_handoff_started_ns')}
        if type(source) is not dict or clean(source)!=clean(observed):
            self.journal.fail('source is not the prior operation observation')
            raise ValueError('source is not the prior operation observation')
        initial=self._cover_source
        def target(row):
            return (row.get('renewal_owner_id'),row.get('input_owner_generation'),
                    row.get('pointer_binding',{}).get('surface'),
                    row.get('target_process_identity',{}).get('digest'),
                    row.get('target_renewal_window_identity',{}).get('digest'))
        try:
            same_target=target(source)==target(initial)
        except (AttributeError,TypeError):
            same_target=False
        if not same_target:
            self.journal.fail('target changed since initial cover')
            raise ValueError('target changed since initial cover')
        started=self.clock()
        try:
            deadline=self.contract.authorize_live(command,source,started,terminal,accepted,
                                                  self.gate,self.backend)
            if self.contract.index==0:
                startup=self.gate.check_submit(command,self.backend,source,terminal=terminal,accepted=accepted)
                if type(startup) is not int:
                    raise ValueError('first-input gate did not produce a deadline')
                deadline=min(deadline,startup)
                self.contract.deadline=deadline
            if self.clock()>=deadline:
                raise ValueError('input deadline expired before submission')
            self.journal.begin(command['id'],min(command['valid_until_ns'],started+5_000_000_000))
            self.pending=command['id']
            self.executor.submit(command['id'],command['steps'],command['expected_sequence'],
                                 command['valid_until_ns'],admission_deadline_ns=deadline)
        except Exception:
            self.journal.fail('door operation dispatch failed')
            raise

    def settle(self):
        if self.pending is None:
            raise ValueError('no pending operation')
        validator=_CoverValidator(self._cover_source) if self.pending=='cover-0' else self.contract
        status=self.journal.complete_if_idle(self.pending,validator,self.executor,self.clock)
        if status=='DONE':
            if self.pending=='cover-0':
                self.cover_done=True
            self.last_completed=self.pending
            self.pending=None
        return status


def route_door_command(command, coordinator, source):
    # A finish request is only allowed after the final validated settle.
    if type(command) is not dict:
        raise ValueError('invalid door command')
    operation=command.get('op')
    if operation=='submit':
        if not coordinator.cover_done:
            coordinator.submit_cover(command,source)
        else:
            coordinator.submit_next(command,source)
        return 'submitted'
    if operation=='door-settle':
        return coordinator.settle()
    if operation=='finish':
        if not coordinator.finished:
            raise ValueError('door sequence is not complete')
        return 'passthrough'
    if operation in ('cancel','clock'):
        return 'passthrough'
    raise ValueError('operation unavailable in door trial')
