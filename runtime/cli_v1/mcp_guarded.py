"""Explicit scoped-X11 owner for the existing retained public MCP transport."""
from copy import deepcopy
from pathlib import Path
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


def open_bridge(display_name, targets, target, directory):
    # Optional Pillow/Xlib dependencies are loaded only for this explicit mode.
    from runtime.guarded_x11_v1.bridge import NativeHandleBridge
    return NativeHandleBridge(display_name, targets, target, directory)


class GuardedSessionOwner(MCPSessionOwner):
    def __init__(self, targets, directory, display_name=None):
        if len(targets) != 1:
            raise ValueError('guarded-x11 requires exactly one explicitly configured target')
        super().__init__(targets, display_name)
        self.target = next(iter(targets))
        self.directory = Path(directory)/('guarded-session-'+self.session_id)
        self.bridge = None
        self.binding_revision = 0

    def get(self):
        if self.state == 'open':
            return self.session
        if self.state != 'unopened':
            raise RuntimeError('guarded session unavailable: '+self.state)
        self.state = 'opening'
        try:
            self.bridge = open_bridge(self.display_name, self.targets, self.target, self.directory)
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
        row['target'] = self.target
        row['observation_sequence'] = self.bridge.sequence if self.bridge else None
        row['review_required'] = self.bridge.review_required if self.bridge else None
        if self.bridge:
            row['binding_revision'] = self.bridge.binding_revision
        return row

    def _with_observation(self, row, source):
        row['source'] = source
        row['observation_report'] = {
            'schema':'agent-interface/runtime-observation-v1', 'status':'returned',
            'observation_id':source['observation_id'], 'observation':source['native'],
            'side_effect_authority':False, 'input_dispatched':False}
        return row

    def invoke_guarded(self, operation, arguments, call_root):
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
            result = method(arguments['alias'], arguments['offset'], tail=arguments['tail'])
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


def register_guarded_tools(server, submit):
    @server.tool()
    async def interface_guarded_activate_window(window_id: StrictInt, source_sequence: StrictInt,
            current_binding_revision: StrictInt, expires_at_ns: StrictInt,
            timeout_ms: Annotated[StrictInt, Field(ge=0,le=2000)],
            review_after_activation: StrictBool=False) -> CallToolResult:
        """Explicitly activate the registered target through ordinary admission.

        Requires exact target window ID, latest delivered source sequence,
        current binding revision and caller-supplied expiry on interface_clock's
        host clock. EWMH activation must be supported by the window manager.
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
                                     feedback: InputFeedback | None=None) -> CallToolResult:
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
        """
        if feedback is not None and not observe_after:
            raise ValueError('feedback requires observe_after=true')
        arguments=dict(alias=alias,offset=offset,tail=tail,
                       interaction=interaction,observe_after=observe_after)
        if feedback is not None:
            arguments['feedback']=feedback.model_dump()
        return await submit('guarded_input',arguments,False,False,detail,observation_refs)

    @server.tool()
    async def interface_guarded_review_window(window_id: StrictInt) -> CallToolResult:
        """Explicitly review a focused window and revoke every old alias.

        Sends no input; even a failed review revokes prior references. A successful
        review returns a fresh source/image for new aliases. This is the native
        bridge's focused-window contract, not authenticated application identity
        or the transient-family inspection contract of persistent-x11 mode.
        """
        return await submit('guarded_review_window',{'window_id':window_id},False,False)
