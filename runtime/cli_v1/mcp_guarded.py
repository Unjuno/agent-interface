"""Explicit scoped-X11 owner for the existing retained public MCP transport."""
from copy import deepcopy
from pathlib import Path
from mcp.types import CallToolResult
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr
from typing import Annotated, Literal
from .mcp_session import MCPSessionOwner


class GroundedReference(BaseModel):
    """An explicit point from the shared delivered source, never an action."""
    model_config = ConfigDict(extra='forbid')
    alias: Annotated[StrictStr, Field(pattern=r'^[a-z][a-z0-9_]{0,31}$')]
    point: Annotated[list[StrictInt], Field(min_length=2, max_length=2)]
    region_size: Annotated[list[Annotated[StrictInt, Field(ge=4, le=96)]],
                           Field(min_length=2, max_length=2)]


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
        if operation == 'guarded_input':
            # From here on a thrown exception may follow emitted input. The
            # transport retains uncertainty; it must not claim no input or retry.
            self.dispatch_attempted = True
            method = bridge.click if arguments['interaction'] == 'click' else bridge.keyboard
            result = method(arguments['alias'], arguments['offset'], tail=arguments['tail'])
            row.update(status=result['status'], result=result)
            if arguments['observe_after']:
                try:
                    self._with_observation(row, bridge.observe())
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
                        offset = bridge.mint(reference.alias, arguments['source_sequence'],
                            reference.point, region_size=tuple(reference.region_size))
                    except Exception as error:
                        # mint may mutate its store before persistence fails. Keep
                        # earlier successes and mark this alias uncertain; no rollback.
                        return dict(row, status='mint_incomplete', minted=minted,
                            source_sequence=arguments['source_sequence'],
                            failed_index=index, failed_alias=reference.alias,
                            failed_alias_state='unknown', error=repr(error),
                            unattempted_aliases=aliases[index+1:], input_dispatched=False)
                    minted.append({'alias':reference.alias, 'offset':offset})
                return dict(row, status='minted', minted=minted,
                            source_sequence=arguments['source_sequence'], input_dispatched=False)
            if operation == 'guarded_mint':
                point, size = arguments['point'], arguments['region_size']
                if len(point) != 2 or len(size) != 2 or any(not 4 <= v <= 96 for v in size):
                    raise ValueError('point pair and region_size pair in 4..96 required')
                offset = bridge.mint(arguments['alias'], arguments['source_sequence'], point,
                                     region_size=tuple(size))
                return dict(row, status='minted', alias=arguments['alias'], offset=offset,
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
        Flat source regions refuse. Returns alias and offset for input. This
        creates no input, target discovery or semantic identity guarantee.
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
        """
        return await submit('guarded_mint_many',{
            'source_sequence':source_sequence,
            'references':[ref.model_dump() for ref in references]},False,False)

    @server.tool()
    async def interface_guarded_input(alias: StrictStr, offset: list[StrictInt], tail: list[dict],
                                     interaction: Literal['click','keyboard']='click',
                                     observe_after: StrictBool=True,
                                     detail: Literal["full","brief"]="full",
                                     observation_refs: StrictBool=False) -> CallToolResult:
        """Use a scoped alias once through fresh pixel guards and ordinary input admission.

        tail uses text, key_chord, wait_update or observe operations, within the
        existing expanded program limit. keyboard emits no pointer click.
        The five-second guarded lease includes typing/waits. Expiry stops later
        presses, interrupts waits and attempts release; partial effects remain.
        Blocking X11 calls are not preempted; no hard real-time bound is promised.
        observe_after captures once immediately after the result; it adds no
        redraw wait. Capture failure retains the input result without replay.
        Inspect result/release separately from feedback and semantic completion.
        detail=brief summarizes known normal exact-match guard details only.
        Failures/unknown shapes remain full; full retrieval never replays input.
        observation_refs=true additionally replaces exact duplicate image metadata
        with a local source.native reference. The reference layer is lossless;
        brief guard summaries remain lossy. Defaults keep the existing full shape.
        """
        return await submit('guarded_input',dict(alias=alias,offset=offset,tail=tail,
                            interaction=interaction,observe_after=observe_after),False,False,detail,observation_refs)

    @server.tool()
    async def interface_guarded_review_window(window_id: StrictInt) -> CallToolResult:
        """Explicitly review a focused window and revoke every old alias.

        Sends no input; even a failed review revokes prior references. A successful
        review returns a fresh source/image for new aliases. This is the native
        bridge's focused-window contract, not authenticated application identity
        or the transient-family inspection contract of persistent-x11 mode.
        """
        return await submit('guarded_review_window',{'window_id':window_id},False,False)
