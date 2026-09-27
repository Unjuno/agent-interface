"""Optional stdio MCP adapter for one explicitly attached native research run."""
import argparse
import hashlib
import json
from pathlib import Path
import threading
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr, model_validator

from agent_review import review_native
from native_exchange_v1 import run
from native_tail_v1 import expand_tail, paced_text_tail


WaitSeconds = Annotated[StrictInt | StrictFloat, Field(ge=0, le=30,
    description="Finite wait seconds in 0..30; zero polls without waiting. No strings or booleans.")]


class NativeDecision(BaseModel):
    """One explicit action, or finish=true to end without another action.

    Action decisions require point and expected_title. Extension fields are
    preserved for the existing harness; this model grants no input authority.
    """
    model_config = ConfigDict(extra='allow', allow_inf_nan=False)
    source_sequence: StrictInt = Field(ge=1, description='Exact sequence of the source image you viewed.')
    point: list[StrictInt | StrictFloat] | None = Field(default=None, min_length=2, max_length=2,
        description=('Observed [x,y] in screen physical pixels; required for click and keyboard context binding. '
                     'Local visual matching needs a stable distinctive patch: avoid uniform fill, blinking carets and changing text. '
                     'For click, stay inside the intended clickable target near a visible border or text; '
                     'do not move to a different control merely to obtain texture. '
                     'For keyboard, choose a visible feature in the intended focused window; '
                     'this point guards context and does not click or select the text destination. '
                     'If visually_flat_source_region is returned with input_dispatched=false, inspect the '
                     'returned image and choose a new point using its new source sequence. No automatic retry.'))
    expected_title: StrictStr | None = Field(default=None,
        description=('Exact complete application window title for feedback (case-sensitive equality, not a substring); '
                     'include the application suffix, e.g. "shape.svg - Inkscape". '
                     'An unmatched title can wait until the feedback timeout and remain pending. '
                     'Required for an action; a title match is not a task success assertion.'))
    interaction: Literal['click','keyboard','observe'] = Field(default='click',
        description=('click then tail, keyboard-only tail, or observe for one fresh capture without input; observe consumes a stage. '
                     'When a returned frame leaves completion unclear, observe can inspect the new state without replaying the action. '
                     'For observe supply only source_sequence and interaction; do not include point, title, tail or finish.'))
    tail: list[dict] = Field(default_factory=list, description=(
        'Explicit ordered native operations. Examples: {"op":"text","text":"190","gap_ms":10}, '
        '{"op":"key_chord","keys":["CTRL","s"]}, '
        '{"op":"key_chord","keys":["Right"],"repeat":18}, '
        '{"op":"wait_update","timeout_ms":50}. Text gap_ms is an integer in 0..1000; it overrides the configured text-gap default (zero disables character gaps). Omit gap_ms to use that default. Text gaps and key repeats expand within the same tail limit: 123 operations for click, 126 for keyboard. No automatic retries.'))
    finish: StrictBool = Field(default=False,
        description=('End and evaluate without new input; requires only source_sequence. Session closes even if scoring fails. '
                     'Evaluation is separate from visual completion; use interaction=observe first if another fresh frame is needed.'))
    finish_after: StrictBool = Field(default=False,
        description='End/evaluate after this explicit action. Do not use if a new dialog may need a decision.')

    @model_validator(mode='after')
    def complete_decision(self):
        if self.interaction == 'observe':
            if set(self.model_dump(exclude_unset=True)) - {'source_sequence', 'interaction'}:
                raise ValueError('observe accepts only source_sequence and interaction; no input or finish flags')
            return self
        if self.finish and self.finish_after:
            raise ValueError('choose finish or finish_after, not both')
        if self.finish:
            if set(self.model_dump(exclude_unset=True)) - {'source_sequence', 'finish'}:
                raise ValueError('finish accepts only source_sequence and finish; use finish_after for an action')
            return self
        if not self.finish and (self.point is None or self.expected_title is None):
            raise ValueError('action requires point and expected_title')
        # Check explicit compact operations before publishing a stage request.
        # Preserve the original payload; harness defaults and runtime admission
        # are still applied by the owner.
        expand_tail(self.tail, max_ops=123 if self.interaction == 'click' else 126)
        if (not self.finish and self.interaction == 'keyboard'
                and not any(op.get('op') in {'text', 'key_chord'} for op in self.tail)):
            raise ValueError('keyboard requires explicit text or key_chord input; '
                             'for a fresh image use only source_sequence and interaction=observe')
        return self


def validate_recorded_tail(root, decision):
    """Check known harness pacing without changing the submitted decision."""
    if decision.finish or decision.interaction == 'observe':
        return
    try:
        policy = json.loads((root/'text-policy.json').read_bytes())
    except FileNotFoundError:
        return  # Historical attached runs may have no recorded policy.
    if (not isinstance(policy, dict) or type(policy.get('gap_ms')) is not int
            or policy['gap_ms'] not in (0, 2, 10)
            or type(policy.get('default_changed')) is not bool):
        raise ValueError('invalid recorded text policy; input was not published by this call')
    capacity = 123 if decision.interaction == 'click' else 126
    try:
        expand_tail(paced_text_tail(decision.tail, policy['gap_ms']), max_ops=capacity)
    except ValueError as error:
        # Explicit syntax already passed NativeDecision; add configuration context,
        # never caller text. This does not reconcile a previous committed request.
        raise ValueError(
            f"native tail exceeds capacity {capacity} after applying recorded default "
            f"gap_ms={policy['gap_ms']}; shorten the batch or explicitly choose per-operation "
            "pacing, then review before a new submission") from error


def session_context(root):
    """Present existing public task/limits, not evaluator output or authority."""
    context = {'authority':'none'}
    for key, filename in [('goal','goal.json'), ('exchange_contract','exchange-contract.json'), ('text_policy','text-policy.json')]:
        path = root/filename
        try:
            data = path.read_bytes()
            value = json.loads(data)
            if not isinstance(value, dict):
                raise ValueError('object required')
            json.dumps(value, allow_nan=False)
            if key == 'exchange_contract' and (
                    value.get('schema') != 'agent-interface/native-exchange-contract-v1'
                    or type(value.get('max_stages')) is not int
                    or not 2 <= value['max_stages'] <= 64):
                raise ValueError('invalid native exchange contract')
            if key == 'text_policy' and (
                    type(value.get('gap_ms')) is not int
                    or value['gap_ms'] not in (0, 2, 10)
                    or type(value.get('default_changed')) is not bool):
                raise ValueError('invalid recorded text policy')
            context[key] = {'status':'recorded', 'value':value,
                            'source':{'path':str(path),'sha256':hashlib.sha256(data).hexdigest()}}
        except FileNotFoundError:
            context[key] = {'status':'unavailable'}
        except (OSError, ValueError, TypeError) as error:
            context[key] = {'status':'needs_review', 'error':str(error)}
    return context


def window_inventory(root, stage):
    """Read only the selected stage's existing listing; never discover/focus."""
    result = {'authority':'none', 'stage':stage,
              'scope':'recorded window listing; not atomic with image, freshness or input authority'}
    if type(stage) is not int or not 1 <= stage <= 64:
        return dict(result, status='needs_review', error='stage 1..64 required')
    path = root/f'windows-{stage}.json'
    try:
        with path.open('rb') as stream:
            raw = stream.read(16385)
        if len(raw) > 16384:
            raise ValueError('recorded listing exceeds 16384-byte presentation limit')
        listing = json.loads(raw)
        if not isinstance(listing, str):
            raise ValueError('recorded listing must be a JSON string')
        return dict(result, status='recorded', text=listing,
                    source={'path':str(path), 'sha256':hashlib.sha256(raw).hexdigest()})
    except FileNotFoundError:
        return dict(result, status='unavailable')
    except (OSError, ValueError) as error:
        return dict(result, status='needs_review', error=str(error))


def content(result):
    """Keep metadata complete; return image once as an MCP image block."""
    metadata = dict(result)
    image = metadata.pop('image', None)
    blocks = [TextContent(type='text', text=json.dumps(metadata, allow_nan=False))]
    if image is not None:
        blocks.append(ImageContent(**image))
    return CallToolResult(content=blocks)


def create_server(run_directory, *, allocation=None):
    root = (allocation.run_directory if allocation is not None
            else Path(run_directory).resolve(strict=True))
    if allocation is None and not root.is_dir():
        raise ValueError('explicit existing native run directory required')
    server = FastMCP('Agent Interface native research session')
    lock = threading.Lock()

    def with_process_snapshot(result):
        continuation = result.get('continuation', {})
        if continuation.get('status') in ('source_available', 'observation_required'):
            result['window_inventory'] = window_inventory(root, continuation.get('stage'))
        # Do not wait for exit, retry input, or let a polling error hide its receipt.
        if allocation is not None:
            try:
                state = dict(allocation.status())
                if 'source_stage' in state:
                    state['initial_source_stage'] = state.pop('source_stage')
            except Exception as error:
                state = {'status': 'needs_review', 'error': str(error), 'authority': 'none',
                         'scope': 'process snapshot unavailable; action result retained'}
            result['allocation'] = state
        return result

    def invoke(operation):
        # One bound run, no concurrent submit/resume processing or automatic retry.
        with lock:
            try:
                return content(operation())
            except Exception as error:
                return CallToolResult(isError=True, content=[TextContent(type='text', text=json.dumps({
                    'status':'client_error', 'error':str(error), 'authority':'none',
                    'program_attempted':None,
                    'recovery':'Inspect the selected stage request/reply. An error does not prove no input; do not replay.'}))])

    if allocation is not None:
        @server.tool(structured_output=False)
        def native_start(timeout: WaitSeconds = 5) -> CallToolResult:
            """Start the configured research allocation once, or wait on that same process.

            Starting/timeout is not permission to restart. Ready returns stage1
            image and public task. End with native_submit finish/finish_after;
            terminal process status alone does not prove task success or cleanup.
            """
            def start():
                state = allocation.start(timeout=timeout)
                if state['status'] != 'ready':
                    return {'allocation':state,'image':None,'authority':'none'}
                result = review_native(root/'source-1.json',root,compact=True)
                result.update(allocation=state, session_context=session_context(root))
                result['window_inventory'] = window_inventory(root, 1)
                return result
            return invoke(start)

        @server.tool(structured_output=False)
        def native_status() -> CallToolResult:
            """Read the launched process state; never starts, kills or restarts it."""
            return invoke(lambda: {'allocation':allocation.status(),'image':None,'authority':'none'})

    if allocation is not None and allocation.owner_lifetime is True:
        @server.tool(structured_output=False)
        def native_stop() -> CallToolResult:
            """Request cooperative stop of this managed allocation, without input.

            Only available in owner-lifetime mode. Closes the owned lifetime pipe;
            in-progress operations can continue until the next boundary. Repeated
            calls do not restart or send signals. Poll native_status for terminal
            process state; stopping is not cleanup completion or task success.
            Exact-request native_resume remains available for prior receipts.
            """
            return invoke(lambda: {'allocation': allocation.request_stop(),
                                  'image': None, 'authority': 'none'})

    @server.tool(structured_output=False)
    def native_observe(stage: StrictInt) -> CallToolResult:
        """Read the retained source for an explicit stage; no recapture or input.

        Includes recorded public goal and exchange limits when available.
        View its image before choosing an action. A historical frame is not fresh
        authority. No latest-stage guessing and no session allocation.
        To request a new frame, use native_submit at the explicit continuation
        stage with only source_sequence and interaction="observe" in decision.
        That consumes one stage without replaying the preceding input.
        """
        def observe():
            if not 1 <= stage <= 64:
                raise ValueError('stage 1..64 required')
            result = review_native(root/f'source-{stage}.json', root, compact=True)
            result['session_context'] = session_context(root)
            result['window_inventory'] = window_inventory(root, stage)
            return result
        return invoke(observe)

    @server.tool(structured_output=False)
    def native_submit(stage: StrictInt, decision: NativeDecision, timeout: WaitSeconds = 5) -> CallToolResult:
        """Submit one explicit decision against its viewed source_sequence.

        Uses existing guarded click/keyboard tail and immutable stage publication.
        Never retry submit after timeout/error. Pending returns decision_sha256:
        use native_resume. Task success is separate from input completion.
        Inspect image_status and continuation separately from feedback_status.
        When continuation.status=source_available, view the returned image and
        use its stage/source_sequence for a new decision; no source-file read is
        needed. This is retained evidence, not freshness or permission to replay.
        When continuation.status=observation_required, the image is historical:
        only explicit observe or finish is accepted; never repeat prior input.
        Managed responses include a process snapshot; it may still be live.
        interaction=observe requests one fresh capture without input; include only
        source_sequence and interaction. It consumes a stage and does not finish.
        It reviews the currently focused window on the private display and revokes
        old target aliases, like the existing post-action handoff; it never focuses.
        """
        def submit():
            if allocation is not None and allocation.status()['status'] != 'ready':
                raise ValueError('managed input requires this server to own a live ready allocation')
            validate_recorded_tail(root, decision)
            return with_process_snapshot(run(root, stage, decision.model_dump(mode='json', exclude_unset=True),
                       timeout=timeout, compact=True))
        return invoke(submit)

    @server.tool(structured_output=False)
    def native_resume(stage: StrictInt, decision_sha256: str, timeout: WaitSeconds = 5) -> CallToolResult:
        """Read/wait for an exact committed request without publishing input.

        Supply the original pending response's stage and SHA256. Missing/changed
        requests refuse. Owner loss requires reconciliation, never restart/replay.
        """
        return invoke(lambda: with_process_snapshot(run(root, stage, resume=True, decision_sha256=decision_sha256,
                                  timeout=timeout, compact=True)))
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    locations = parser.add_mutually_exclusive_group(required=True)
    locations.add_argument('--run-directory', help='attach an existing harness run')
    locations.add_argument('--allocation-directory', help='fresh parent directory for an explicitly started private run')
    parser.add_argument('--app', choices=('calc','inkscape','calc-inkscape'))
    parser.add_argument('--seed',type=int,default=991116)
    parser.add_argument('--max-stages',type=int,default=4)
    parser.add_argument('--harness-python', help='Python with existing GUI harness dependencies')
    parser.add_argument('--text-gap-ms', type=int, choices=(0,2,10), default=None,
                        help='explicit existing harness text pacing policy (managed mode only; default 0)')
    parser.add_argument('--owner-lifetime', action='store_true',
                        help='experimental managed pipe lifetime; cooperative boundaries only')
    args = parser.parse_args()
    allocation = None
    if args.allocation_directory:
        if args.app is None:
            parser.error('--allocation-directory requires --app')
        from native_allocation_v1 import NativeAllocation
        allocation = NativeAllocation(args.allocation_directory,args.app,seed=args.seed,
                                      max_stages=args.max_stages,python=args.harness_python,
                                      text_gap_ms=0 if args.text_gap_ms is None else args.text_gap_ms,
                                      owner_lifetime=args.owner_lifetime)
    elif args.app or args.harness_python or args.text_gap_ms is not None or args.owner_lifetime:
        parser.error('--app/--harness-python/--text-gap-ms/--owner-lifetime require --allocation-directory')
    create_server(args.run_directory,allocation=allocation).run(transport='stdio')
