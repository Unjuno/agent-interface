"""Explicit scoped-X11 owner for the existing retained public MCP transport."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import time
from mcp.types import CallToolResult
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator
from typing import Annotated, Literal
from .mcp_session import MCPSessionOwner


class GroundedReference(BaseModel):
    """An explicit point from the shared delivered source, never an action."""
    model_config = ConfigDict(extra='forbid')
    alias: Annotated[StrictStr, Field(pattern=r'^[a-z][a-z0-9_]{0,31}$')]
    point: Annotated[list[StrictInt], Field(min_length=2, max_length=2)]
    region_size: Annotated[list[Annotated[StrictInt, Field(ge=4, le=96)]],
                           Field(min_length=2, max_length=2)]


class InputFeedback(BaseModel):
    """Caller-selected read-only title cue; never input authority or a task score."""
    model_config = ConfigDict(extra='forbid')
    expected_title: Annotated[StrictStr, Field(min_length=1)]
    rejected_titles: list[Annotated[StrictStr, Field(min_length=1)]] = Field(default_factory=list)
    timeout_ms: Annotated[StrictInt, Field(ge=0, le=10000)] = 2000

    @model_validator(mode='after')
    def distinct_expected_title(self):
        if self.expected_title in self.rejected_titles:
            raise ValueError('expected title cannot also be rejected')
        return self


def open_bridge(display_name, targets, target, directory, *, process_identity=False, query_worker=False, observation_worker=False, window_lifecycle=False):
    # Optional Pillow/Xlib dependencies are loaded only for this explicit mode.
    from runtime.guarded_x11_v1.bridge import NativeHandleBridge
    options = dict(process_identity=process_identity,query_worker=query_worker)
    if observation_worker: options['observation_worker'] = True
    if window_lifecycle: options['window_lifecycle'] = True
    return NativeHandleBridge(display_name, targets, target, directory,**options)


class GuardedSessionOwner(MCPSessionOwner):
    def __init__(self, targets, directory, display_name=None, *, process_identity=False, query_worker=False, observation_worker=False, window_lifecycle=False):
        if type(process_identity) is not bool:
            raise ValueError('process_identity must be a boolean')
        if type(query_worker) is not bool or (query_worker and not process_identity):
            raise ValueError('query_worker requires explicit process_identity=True')
        if type(observation_worker) is not bool or (observation_worker and not query_worker):
            raise ValueError('observation_worker requires explicit query_worker=True')
        if type(window_lifecycle) is not bool or (window_lifecycle and not query_worker):
            raise ValueError('window_lifecycle requires explicit query_worker=True')
        if len(targets) != 1:
            raise ValueError('guarded-x11 requires exactly one explicitly configured target')
        super().__init__(targets, display_name)
        self.target = next(iter(targets))
        self.directory = Path(directory)/('guarded-session-'+self.session_id)
        self.bridge = None
        self.binding_revision = 0
        self.process_identity = process_identity
        self.query_worker = query_worker
        self.observation_worker = observation_worker
        self.window_lifecycle = window_lifecycle

    def get(self):
        if self.state == 'open':
            return self.session
        if self.state != 'unopened':
            raise RuntimeError('guarded session unavailable: '+self.state)
        self.state = 'opening'
        try:
            options = {'process_identity':True} if self.process_identity else {}
            if self.query_worker: options['query_worker'] = True
            if self.observation_worker: options['observation_worker'] = True
            if self.window_lifecycle: options['window_lifecycle'] = True
            self.bridge = open_bridge(self.display_name, self.targets, self.target, self.directory, **options)
            self.session = self.bridge.session
            self.state = 'open'
            return self.session
        except Exception as error:
            self.state = 'failed'
            self.error = repr(error)
            raise

    def snapshot(self):
        row = super().snapshot()
        row['mode'] = 'guarded-x11'
        row['process_identity'] = self.process_identity
        row['query_worker'] = self.query_worker
        row['observation_worker'] = self.observation_worker
        row['window_lifecycle'] = self.window_lifecycle
        observations = getattr(self.bridge,'_observations',None)
        row['observations'] = observations.snapshot() if observations is not None else None
        worker = getattr(self.bridge,'_target_queries',None)
        row['target_queries'] = worker.snapshot() if worker is not None else None
        row['target'] = self.target
        row['observation_sequence'] = self.bridge.sequence if self.bridge else None
        row['review_required'] = self.bridge.review_required if self.bridge else None
        if self.bridge:
            row['binding_revision'] = self.bridge.binding_revision
        return row

    def close(self):
        if self.bridge is not None:
            consume_close = getattr(self.bridge,'_consume_close',None)
            if callable(consume_close): consume_close()
            elif self.query_worker: self.bridge.stop_target_queries()
        return super().close()

    def cancel_guarded(self, token):
        if self.state != 'open' or self.bridge is None or not self.query_worker:
            return {'status':'not_active','input_dispatched':False,'release_confirmed':False}
        return self.bridge.request_cancel(token)

    def _with_observation(self, row, source):
        row['source'] = source
        row['observation_report'] = {
            'schema':'agent-interface/runtime-observation-v1', 'status':'returned',
            'observation_id':source['observation_id'], 'observation':source['native'],
            'side_effect_authority':False, 'input_dispatched':False}
        return row

    @contextmanager
    def input_guard(self, alias, offset, *, tail, verify):
        """Opt-in synchronous dependency check for a frozen keyboard program.

        Register around an explicit invocation on this open Python owner.
        The callback receives stage, copied current native source and RGB image;
        exactly True permits continuation only after existing guards pass.
        No MCP endpoint, capture loop, input authority or automatic renewal.
        """
        if self.state != 'open' or self.bridge is None or self.session is None:
            raise RuntimeError('input guard requires this open guarded owner')
        with self.bridge.input_guard(alias, offset, tail=tail, verify=verify):
            yield

    def run_compiled(self, interface, bindings, *, call_root, perceive,
                     verify_effect, cancelled=lambda: False):
        """Run one explicit graph on this already-open Python owner.

        Ground references first. Callbacks are trusted read-only caller code,
        not a model, sensor or independent persistence oracle. Use a fresh call
        directory; no reopen, retry, remint or extra final capture is performed.
        The existing graph retains its raw evidence in the bridge directory.
        The returned method verdict and delivered feedback remain distinct from
        independently verified task success. This is not an MCP tool endpoint.
        """
        started_ns = time.monotonic_ns()
        if self.state != 'open' or self.bridge is None or self.session is None:
            raise RuntimeError('compiled method requires this open guarded owner')
        if self.bridge.review_required or self.session.recovery_required:
            raise RuntimeError('compiled method requires reviewed, recovered owner')
        if not all(callable(fn) for fn in (perceive, verify_effect, cancelled)):
            raise ValueError('explicit callable perception, effect and cancellation required')
        from runtime.guarded_x11_v1 import compiled
        from .review import present_result
        root = Path(call_root)
        root.mkdir(parents=True, exist_ok=False)
        bridge = self.bridge
        previous_sequence = bridge.sequence
        # An exception can follow partial input. Keep cleanup on this same
        # connection even when no terminal receipt reached the caller.
        self.dispatch_attempted = True
        try:
            bridge.backend.configure_capture_artifacts(root/'images', retain_rgb=True)
            receipt = compiled.run(bridge, interface, bindings, perceive=perceive,
                                   verify_effect=verify_effect, cancelled=cancelled)
        except Exception as error:
            bridge.review_required = True
            self.error = repr(error)
            raise
        feedback = None
        if receipt['observations']:
            try:
                sequence = receipt['observations'][-1]['sequence']
                if (type(sequence) is not int or sequence <= previous_sequence
                        or sequence != bridge.sequence):
                    raise ValueError('final graph observation no longer matches this owner')
                source, _ = bridge.history[sequence]
                feedback = present_result({
                    'schema':'agent-interface/runtime-observation-v1',
                    'status':'returned', 'observation_id':source['observation_id'],
                    'observation':source['native'], 'input_dispatched':False,
                    'side_effect_authority':False}, root, compact=True, report_refs=True)
                if feedback.get('image_status') != 'image':
                    bridge.review_required = True
            except Exception as error:
                bridge.review_required = True
                feedback = {'image_status':'needs_review', 'image':None,
                            'error':repr(error), 'replay_allowed':False,
                            'scope':'Method receipt retained; final feedback unavailable. No replay.'}
        session = self.snapshot()
        completed_ns = time.monotonic_ns()
        return {'method_receipt':receipt, 'feedback':feedback, 'session':session,
                'owner_timing':{'clock':'time.monotonic_ns',
                    'scope':'successful run_compiled method call through feedback and session snapshot',
                    'started_ns':started_ns, 'completed_ns':completed_ns,
                    'elapsed_ns':completed_ns-started_ns},
                'task_success':None, 'replay_allowed':False}

    def invoke_guarded(self, operation, arguments, call_root):
        if operation == 'guarded_recover_input':
            if self.state != 'open' or self.bridge is None or self.session is None:
                return dict(operation=operation,status='refused',error='RECOVERY_REQUIRES_OPEN_SESSION',
                            release_attempted=False,authority_granted=False,task_success=None,replay_allowed=False)
            report = self.bridge.recover_input(arguments['current_binding_revision'])
            if report.get('release_attempted'): self.dispatch_attempted = True
            self.binding_revision = self.bridge.binding_revision
            return dict(report,operation=operation)
        cue = None
        if operation == 'guarded_input' and arguments.get('feedback') is not None:
            cue = InputFeedback.model_validate(arguments['feedback'])
            if not arguments['observe_after']:
                raise ValueError('feedback requires observe_after=true')
        if operation == 'guarded_mint_many':
            # Validate the complete batch before opening a connection or minting.
            references = [GroundedReference.model_validate(ref) for ref in arguments['references']]
            aliases = [ref.alias for ref in references]
            if not 1 <= len(references) <= 8 or len(set(aliases)) != len(aliases):
                return {'operation':operation, 'status':'refused',
                        'error':'one to eight unique aliases required', 'input_dispatched':False,
                        'minted':[], 'task_success':None, 'replay_allowed':False}
        self.get()
        bridge = self.bridge
        # Guarded observations consume the current capture's producer RGB.
        bridge.backend.configure_capture_artifacts(Path(call_root)/'images', retain_rgb=True)
        row = {'operation':operation, 'task_success':None, 'replay_allowed':False}
        if operation == 'guarded_activate_window':
            # A failed reply may follow a WM request with a delayed effect.
            self.dispatch_attempted = True
            activation_arguments = dict(arguments)
            review_requested = activation_arguments.pop('review_after_activation', False)
            result = bridge.activate_window(**activation_arguments)
            row.update(status=result['status'], result=result)
            if review_requested:
                row['feedback_status'] = 'review_not_attempted'
                releases = result.get('execution', {}).get('releases', [])
                neutral = bool(releases) and all(
                    release.get('verified') is True and release.get('keys_down') == []
                    and release.get('buttons_down') == [] for release in releases)
                if result['status'] == 'completed' and neutral and not bridge.session.recovery_required:
                    # Explicit composition only: never ground a coordinate, edit,
                    # retry activation or certify task success from this image.
                    try:
                        review = bridge.review_window(arguments['window_id'])
                    except Exception as error:
                        # The WM request already happened. Preserve its receipt
                        # and block editing even if review persistence failed.
                        bridge.review_required = True
                        row.update(status='needs_review', feedback_status='review_failed',
                                   review_error=repr(error))
                        return row
                    self.binding_revision = bridge.binding_revision
                    self.targets[self.target] = bridge.backend.targets[self.target].id
                    row.update(status=review['status'], review=review,
                               feedback_status='review_returned')
                    if review['status'] == 'reviewed':
                        self._with_observation(row, review['observation'])
            return row
        if operation == 'guarded_input':
            # From here on a thrown exception may follow emitted input. The
            # transport retains uncertainty; it must not claim no input or retry.
            self.dispatch_attempted = True
            method = {'click': bridge.click, 'keyboard': bridge.keyboard,
                      'move': bridge.move}[arguments['interaction']]
            if self.query_worker:
                with bridge.cancellation_scope(Path(call_root).name):
                    result = method(arguments['alias'], arguments['offset'], tail=arguments['tail'])
            else:
                result = method(arguments['alias'], arguments['offset'], tail=arguments['tail'])
            if result.get('status') == 'execution_failed':
                # A terminal failure can follow partial task effects even when
                # same-owner release was verified. Require fresh visual review
                # before another input can reuse the still-live source alias.
                bridge.review_required = True
            row.update(status=result['status'], result=result)
            if cue is not None:
                row['feedback_status'] = 'cue_not_attempted'
                releases = result.get('execution', {}).get('releases', [])
                neutral = bool(releases) and all(
                    release.get('verified') is True and release.get('keys_down') == []
                    and release.get('buttons_down') == [] for release in releases)
                if (result['status'] == 'completed' and neutral
                    and result.get('recovery_required') is not True
                    and not bridge.session.recovery_required and not bridge.review_required):
                    try:
                        feedback = bridge.feedback(**cue.model_dump())
                        row.update(feedback=feedback, feedback_status='cue_returned')
                        if 'observation' in feedback:
                            self._with_observation(row, feedback['observation'])
                        if feedback['status'] != 'matched':
                            row['status'] = 'needs_review'
                        if feedback['status'] == 'needs_review':
                            bridge.review_required = True
                    except Exception as error:
                        # Input already happened. Retain its original receipt;
                        # never substitute a no-input claim or replay it.
                        bridge.review_required = True
                        row.update(status='needs_review', feedback_status='cue_failed',
                                   feedback_error=repr(error))
                    return row
            if arguments['observe_after']:
                try:
                    self._with_observation(row, bridge.observe())
                    if cue is None:
                        row['feedback_status'] = 'captured'
                except Exception as error:
                    row.update(feedback_status='observation_failed', observation_error=repr(error))
            else:
                row['feedback_status'] = 'not_requested'
            return row
        try:
            if operation == 'guarded_observe':
                return self._with_observation(dict(row, status='observed', input_dispatched=False), bridge.observe())
            if operation == 'guarded_mint_many':
                minted = []
                for index, reference in enumerate(references):
                    try:
                        grounded = bridge.mint_reference(reference.alias, arguments['source_sequence'],
                            reference.point, region_size=tuple(reference.region_size))
                    except Exception as error:
                        # mint may mutate its store before persistence fails. Keep
                        # earlier successes and mark this alias uncertain; no rollback.
                        return dict(row, status='mint_incomplete', minted=minted,
                            source_sequence=arguments['source_sequence'],
                            failed_index=index, failed_alias=reference.alias,
                            failed_alias_state='unknown', error=repr(error),
                            unattempted_aliases=aliases[index+1:], input_dispatched=False)
                    minted.append({'alias':reference.alias, **grounded})
                return dict(row, status='minted', minted=minted,
                            source_sequence=arguments['source_sequence'], input_dispatched=False)
            if operation == 'guarded_mint':
                point, size = arguments['point'], arguments['region_size']
                if len(point) != 2 or len(size) != 2 or any(not 4 <= v <= 96 for v in size):
                    raise ValueError('point pair and region_size pair in 4..96 required')
                grounded = bridge.mint_reference(arguments['alias'], arguments['source_sequence'], point,
                                     region_size=tuple(size))
                return dict(row, status='minted', alias=arguments['alias'], **grounded,
                            source_sequence=arguments['source_sequence'], input_dispatched=False)
            if operation == 'guarded_review_window':
                result = bridge.review_window(arguments['window_id'])
                self.binding_revision = bridge.binding_revision
                self.targets[self.target] = bridge.backend.targets[self.target].id
                row.update(status=result['status'], review=result, input_dispatched=False)
                if result.get('status') == 'reviewed':
                    self._with_observation(row, result['observation'])
                return row
            raise ValueError('unknown guarded operation')
        except Exception as error:
            return dict(row, status='refused', error=repr(error), input_dispatched=False)


def register_guarded_tools(server, submit, *, cancel=None):
    @server.tool()
    async def interface_guarded_recover_input(current_binding_revision: StrictInt,
            wait_for_result_ms: Annotated[StrictInt, Field(ge=0,le=10000)] | None=None) -> CallToolResult:
        """Explicitly attempt tracked-input release once on this open guarded owner.

        Requires recovery_required=true and the current binding revision. The
        serialized input slot prevents a second writer during pending input or
        cleanup. Accepted recovery consumes the revision and revokes old aliases
        before one release/readback attempt, including on failure. A stale
        request cannot repeat it. Verified neutrality clears only the input
        recovery block; review the window and mint fresh aliases before choosing
        new input. No capture, reconnect, program replay, task success or lease.
        Blocking platform I/O can leave this call pending; inspect results and
        never replay an uncertain request automatically. Retired workers remain
        retired and require explicitly closing the session.
        Optional wait_for_result_ms ends only the response await; pending returns
        the original call ID without release confirmation. The same worker keeps
        cleanup custody. Retrieve its result; never resubmit because it is pending.
        """
        options = {} if wait_for_result_ms is None else dict(wait_for_result_ms=wait_for_result_ms)
        return await submit('guarded_recover_input',dict(current_binding_revision=current_binding_revision),False,False,**options)
    if cancel is not None:
        @server.tool()
        async def interface_guarded_cancel(call_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')]) -> CallToolResult:
            """Request cancellation of this running guarded-input call, bypassing the busy slot.

            Get the call ID from interface_results. This publishes retained local
            state only; no input or cleanup is injected here. Acknowledgement is
            not release confirmation. Inspect the original result/cleanup; never
            replay uncertain input. Old/unknown call IDs cannot cancel a new call.
            """
            return cancel(call_id)
    @server.tool()
    async def interface_guarded_activate_window(window_id: StrictInt, source_sequence: StrictInt,
            current_binding_revision: StrictInt, expires_at_ns: StrictInt,
            timeout_ms: Annotated[StrictInt, Field(ge=0,le=2000)],
            review_after_activation: StrictBool=False) -> CallToolResult:
        """Explicitly activate the registered target through ordinary admission.

        Requires exact target window ID, latest retained bridge source sequence,
        current binding revision and caller-supplied expiry on interface_clock's
        host clock. Recovery-cleared history requires a new observation. Pinned
        source context, selected process generation and original expiry are
        rechecked before the WM request; this is not atomic server acceptance
        or a current-pixel guarantee. EWMH must be supported by the window manager.
        Sends no text/click. Success is a momentary focus
        check, not visual or task confirmation. After admitted or uncertain
        activation, explicitly review the window with guarded_review_window,
        review its image, then mint a new alias and choose a new action.
        Timeout is a polling budget, not a blocking X11 deadline; the WM may
        apply the request later. No replay or lease renewal. Unverified input
        cleanup blocks activation. This does not clear a caller's STOP policy.
        review_after_activation=true explicitly requests window review and its
        exact image in this same reply, only after completed activation with
        verified neutral release. Default false retains the separate-review
        path. Review the returned image before fresh grounding or any editing.
        Failed activation never triggers review or retry; a failed review keeps
        the activation receipt and requires a new caller decision.
        """
        return await submit('guarded_activate_window',dict(window_id=window_id,
            source_sequence=source_sequence,current_binding_revision=current_binding_revision,
            expires_at_ns=expires_at_ns,timeout_ms=timeout_ms,
            review_after_activation=review_after_activation),False,False)

    @server.tool()
    async def interface_guarded_observe(observation_refs: StrictBool=False) -> CallToolResult:
        """Capture the full screen on the configured X11 connection; send no input.

        Returns a source.sequence and image for explicit grounding. Capture is
        not a redraw or task-completion acknowledgement. No implicit polling.
        observation_refs=true references exact duplicate native image metadata at
        source.native within this response; image delivery is unchanged.
        """
        return await submit('guarded_observe', {}, False, False, observation_refs=observation_refs)

    @server.tool()
    async def interface_guarded_mint(alias: StrictStr, source_sequence: StrictInt,
                                    point: list[StrictInt], region_size: list[StrictInt]) -> CallToolResult:
        """Name an explicitly image-grounded point from an exact delivered source.

        point=[screen_x,screen_y]; region_size=[width,height], each 4..96 pixels.
        Flat source regions refuse. Returns alias, offset and finite lifetime
        in this execution host's monotonic clock; compare with interface_clock.
        Lifetime does not guarantee fresh pixels or admission; retained lookup
        never renews it. After a pause, explicitly observe/review and ground a
        new alias if needed. Creates no input or semantic identity guarantee.
        """
        return await submit('guarded_mint', dict(alias=alias,source_sequence=source_sequence,
                            point=point,region_size=region_size),False,False)

    @server.tool()
    async def interface_guarded_mint_many(source_sequence: StrictInt,
            references: Annotated[list[GroundedReference], Field(min_length=1,max_length=8)]) -> CallToolResult:
        """Register 1..8 explicit points from one already delivered image, without input.

        Each reference has alias, point=[screen_x,screen_y], region_size=[width,height].
        Aliases must be unique; all syntax is validated before minting. This is
        sequential registration, not an action queue or atomic transaction.
        On failure, earlier minted references remain; failed_alias_state is unknown
        because registration may precede persistence failure. Later aliases are
        unattempted. Inspect the result; do not replay or reuse the failed alias.
        Each later input still requires fresh visual guards and ordinary admission.
        Each successful reference includes its own finite lifetime in this host's
        monotonic clock. Reading retained results does not renew that deadline.
        """
        return await submit('guarded_mint_many',{
            'source_sequence':source_sequence,
            'references':[ref.model_dump() for ref in references]},False,False)

    @server.tool()
    async def interface_guarded_input(alias: StrictStr, offset: list[StrictInt], tail: list[dict],
                                     interaction: Literal['click','keyboard','move']='click',
                                     observe_after: StrictBool=True,
                                     detail: Literal["full","brief"]="full",
                                     observation_refs: StrictBool=False,
                                     feedback: InputFeedback | None=None,
                                     wait_for_result_ms: Annotated[StrictInt, Field(ge=0,le=10000)] | None=None) -> CallToolResult:
        """Use a scoped alias once through fresh pixel guards and ordinary input admission.

        tail uses text, key_chord, wait_update or observe operations, within the
        existing expanded program limit. keyboard emits no pointer click.
        move emits guarded pointer motion without pressing; its tail permits
        only wait_update and observe. Hover can change pixels. Review its fresh
        image and explicitly mint a new reference before a later click; no
        automatic re-grounding, click or replay follows motion.
        The five-second guarded lease includes typing/waits. Expiry stops later
        presses, interrupts waits and attempts release; partial effects remain.
        Blocking X11 calls are not preempted; no hard real-time bound is promised.
        observe_after captures once immediately after the result; it adds no
        redraw wait. Capture failure retains the input result without replay.
        feedback explicitly waits for expected_title or a rejected title after
        completed input with verified neutral release. Its timeout_ms is 0..10000;
        observe_after must be true. The returned image is the cue capture, without
        an extra immediate capture. Pending/rejected/unstable cues return
        needs_review while retaining the original result. Title matching grants
        no authority and is not durable task completion; a title may predate input.
        No replay, new alias, lease renewal or automatic next action follows.
        Inspect result/release separately from feedback and semantic completion.
        detail=brief summarizes known normal exact-match guard details only.
        Failures/unknown shapes remain full; full retrieval never replays input.
        observation_refs=true additionally replaces exact duplicate image metadata
        with a local source.native reference. The reference layer is lossless;
        brief guard summaries remain lossy. Defaults keep the existing full shape.
        Optional wait_for_result_ms limits the local response await, not input
        execution/lease/cleanup. Pending names one queued/running original call;
        it confirms neither release nor task success. The same worker can still
        run after this response and retains its busy slot. Retrieve with
        interface_results(call_id); never replay a pending/uncertain invocation.
        Default null awaits the original terminal response. This is cooperative
        scheduling, not a hard transport or physical-release time bound.
        """
        if feedback is not None and not observe_after:
            raise ValueError('feedback requires observe_after=true')
        arguments=dict(alias=alias,offset=offset,tail=tail,
                       interaction=interaction,observe_after=observe_after)
        if feedback is not None:
            arguments['feedback']=feedback.model_dump()
        options = {} if wait_for_result_ms is None else dict(wait_for_result_ms=wait_for_result_ms)
        return await submit('guarded_input',arguments,False,False,detail,observation_refs,**options)

    @server.tool()
    async def interface_guarded_review_window(window_id: StrictInt) -> CallToolResult:
        """Explicitly review a focused window and revoke every old alias.

        Sends no input; even a failed review revokes prior references. A successful
        review returns a fresh source/image for new aliases. This is the native
        bridge's focused-window contract, not authenticated application identity
        or the transient-family inspection contract of persistent-x11 mode.
        """
        return await submit('guarded_review_window',{'window_id':window_id},False,False)
