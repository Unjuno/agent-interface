"""Bind one post-cross visual check to one caller write.

Feed only rows already accepted by the single standard-protocol reader. This
bridge does not replace the runtime contract's live admission or focus checks.
"""
from copy import deepcopy
from pathlib import Path
from map01_east_return_visual_guard import check, MAX_FRAME_AGE_NS


def require_no_pending_output(buffer, selector):
    """Fail closed if a received or readable runtime row is unprocessed."""
    if type(buffer) is not bytes or buffer or selector.select(0):
        raise ValueError('runtime output pending before input write')


def require_new_frame(source, expected_stage):
    if (type(source) is not dict or source.get('event')!='observation' or source.get('id')!=expected_stage
            or type(source.get('sequence')) is not int or source['sequence']<1
            or source.get('image_reused') is not False or type(source.get('image')) is not str
            or Path(source['image']).name!=f"{source['sequence']:03d}.png"):
        raise ValueError('guard requires a newly captured source frame')


class EastReturnCallerGate:
    def __init__(self, *, reference, reference_sha256, runtime_dir, identity, arm='east-return'):
        if arm not in ('east-return','east-return-turn75'):
            raise ValueError('unsupported registered east-return arm')
        self.arm=arm
        self.reference=reference
        self.reference_sha256=reference_sha256
        self.runtime_dir=runtime_dir
        self.identity=deepcopy(identity)
        self.typed=None
        self.full=None
        self.transition=None
        self.terminal=None
        self.settlement=None
        self.state='collecting'
        self.receipt=None
        self.command=None
        self.bound_source=None

    def receive(self, row):
        if type(row) is not dict:
            self.state='blocked'
            raise ValueError('invalid caller event')
        if self.state!='collecting':
            self.state='blocked'
            raise ValueError('new event after guard preparation')
        event=row.get('event'); identifier=row.get('id')
        if event in ('typed_observation','observation'):
            if self.terminal is not None:
                self.state='blocked';raise ValueError('observation after terminal')
            if identifier!='reverse-cross':
                # Only the cross's last pair is eligible; no old pair survives.
                self.typed=None;self.full=None
                return
            if event=='typed_observation':
                self.typed=deepcopy(row);self.full=None
            else:
                if self.typed is None or self.typed.get('sequence')!=row.get('sequence'):
                    self.state='blocked';raise ValueError('unpaired full observation')
                self.full=deepcopy(row)
        elif event=='input_release_transition' and identifier=='reverse-cross':
            if self.transition is not None or self.terminal is not None:
                self.state='blocked';raise ValueError('duplicate or late release')
            self.transition=deepcopy(row)
        elif event=='terminal' and identifier=='reverse-cross':
            if self.terminal is not None or self.transition is None or self.full is None:
                self.state='blocked';raise ValueError('terminal before cross evidence')
            self.terminal=deepcopy(row)
        elif event=='door_settle' and row.get('operation_id')=='reverse-cross':
            if row.get('status')=='WAIT':
                return
            if row.get('status')!='DONE' or self.terminal is None or self.settlement is not None:
                self.state='blocked';raise ValueError('cross settlement invalid')
            self.settlement=deepcopy(row)
        elif event in ('rejected','input_release_unverified'):
            self.state='blocked';raise ValueError('runtime rejected or release unknown')

    def _protocol_matches(self, protocol, command):
        identity=self.identity
        expected_identity=(identity['surface'],identity['owner'],identity['generation'],
                           identity['process_digest'],identity['window_digest'])
        return (getattr(protocol,'ready',False) is True
                and getattr(protocol,'reverse_arm',None)==self.arm
                and getattr(protocol,'pending',None)=='east-turn-1'
                and getattr(protocol,'typed',None) is None
                and getattr(protocol,'identity',None)==expected_identity
                and getattr(protocol,'latest',None)==self.full
                and type(command) is dict and command.get('op')=='submit'
                and command.get('id')=='east-turn-1'
                and command.get('steps')==[{'op':'hold','keys':['Right'],'duration_ms':600}]
                and command.get('expected_sequence')==self.full.get('sequence'))

    def prepare(self, command, protocol, *, clock):
        if self.state!='collecting':
            raise ValueError('guard not available')
        self.state='blocked'
        if (self.settlement is None or self.full is None or self.typed is None
                or self.transition is None or self.terminal is None
                or not self._protocol_matches(protocol,command)):
            raise ValueError('cross or caller state incomplete')
        require_new_frame(self.full,'reverse-cross')
        expected=dict(self.identity,sequence=self.full['sequence'])
        receipt=check(self.full,reference=self.reference,reference_sha256=self.reference_sha256,
                      runtime_dir=self.runtime_dir,terminal=self.terminal,transition=self.transition,
                      settlement=self.settlement,expected=expected,typed=self.typed,clock=clock)
        self.receipt=deepcopy(receipt)
        if receipt.get('passed') is not True:
            raise ValueError('post-cross image gate refused')
        self.command=deepcopy(command);self.bound_source=deepcopy(self.full)
        self.state='prepared'
        return deepcopy(receipt)

    def before_write(self, command, protocol, *, now, absolute_deadline):
        if self.state!='prepared':
            raise ValueError('guard not prepared or already consumed')
        self.state='blocked'  # Consume before I/O; even an ambiguous write cannot be replayed.
        if (type(now) is not int or type(absolute_deadline) is not int
                or type(command.get('valid_until_ns')) is not int
                or now>=absolute_deadline or now>=command['valid_until_ns']
                or not 0<=now-self.receipt['capture_ns']<MAX_FRAME_AGE_NS
                or command!=self.command or self.full!=self.bound_source
                or not self._protocol_matches(protocol,command)):
            raise ValueError('caller changed or deadline expired before write')
        self.state='consumed'
