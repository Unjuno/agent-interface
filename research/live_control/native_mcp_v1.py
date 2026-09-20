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
        description='Observed [x,y] in screen physical pixels; required for click and keyboard context binding.')
    expected_title: StrictStr | None = Field(default=None,
        description='Expected application title for feedback; required for an action, not a task success assertion.')
    interaction: Literal['click','keyboard'] = Field(default='click',
        description='click then tail, or keyboard-only tail with the same visual context checks.')
    tail: list[dict] = Field(default_factory=list, description=(
        'Explicit ordered native operations. Examples: {"op":"text","text":"190"}, '
        '{"op":"key_chord","keys":["CTRL","s"]}, '
        '{"op":"key_chord","keys":["Right"],"repeat":18}, '
        '{"op":"wait_update","timeout_ms":50}. No automatic waits or retries.'))
    finish: StrictBool = Field(default=False,
        description='End and evaluate without new input; requires only source_sequence. Session closes even if scoring fails.')
    finish_after: StrictBool = Field(default=False,
        description='End/evaluate after this explicit action. Do not use if a new dialog may need a decision.')

    @model_validator(mode='after')
    def complete_decision(self):
        if self.finish and self.finish_after:
            raise ValueError('choose finish or finish_after, not both')
        if self.finish:
            if set(self.model_dump(exclude_unset=True)) - {'source_sequence', 'finish'}:
                raise ValueError('finish accepts only source_sequence and finish; use finish_after for an action')
            return self
        if not self.finish and (self.point is None or self.expected_title is None):
            raise ValueError('action requires point and expected_title')
        return self


def session_context(root):
    """Present existing public task/limits, not evaluator output or authority."""
    context = {'authority':'none'}
    for key, filename in [('goal','goal.json'), ('exchange_contract','exchange-contract.json')]:
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
            context[key] = {'status':'recorded', 'value':value,
                            'source':{'path':str(path),'sha256':hashlib.sha256(data).hexdigest()}}
        except FileNotFoundError:
            context[key] = {'status':'unavailable'}
        except (OSError, ValueError, TypeError) as error:
            context[key] = {'status':'needs_review', 'error':str(error)}
    return context


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
                return result
            return invoke(start)

        @server.tool(structured_output=False)
        def native_status() -> CallToolResult:
            """Read the launched process state; never starts, kills or restarts it."""
            return invoke(lambda: {'allocation':allocation.status(),'image':None,'authority':'none'})

    @server.tool(structured_output=False)
    def native_observe(stage: StrictInt) -> CallToolResult:
        """Read the retained source for an explicit stage; no recapture or input.

        Includes recorded public goal and exchange limits when available.
        View its image before choosing an action. A historical frame is not fresh
        authority. No latest-stage guessing and no session allocation.
        """
        def observe():
            if not 1 <= stage <= 64:
                raise ValueError('stage 1..64 required')
            result = review_native(root/f'source-{stage}.json', root, compact=True)
            result['session_context'] = session_context(root)
            return result
        return invoke(observe)

    @server.tool(structured_output=False)
    def native_submit(stage: StrictInt, decision: NativeDecision, timeout: WaitSeconds = 5) -> CallToolResult:
        """Submit one explicit decision against its viewed source_sequence.

        Uses existing guarded click/keyboard tail and immutable stage publication.
        Never retry submit after timeout/error. Pending returns decision_sha256:
        use native_resume. Task success is separate from input completion.
        Managed responses include a process snapshot; it may still be live.
        """
        def submit():
            if allocation is not None and allocation.status()['status'] != 'ready':
                raise ValueError('managed input requires this server to own a live ready allocation')
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
    args = parser.parse_args()
    allocation = None
    if args.allocation_directory:
        if args.app is None:
            parser.error('--allocation-directory requires --app')
        from native_allocation_v1 import NativeAllocation
        allocation = NativeAllocation(args.allocation_directory,args.app,seed=args.seed,
                                      max_stages=args.max_stages,python=args.harness_python,
                                      text_gap_ms=0 if args.text_gap_ms is None else args.text_gap_ms)
    elif args.app or args.harness_python or args.text_gap_ms is not None:
        parser.error('--app/--harness-python/--text-gap-ms require --allocation-directory')
    create_server(args.run_directory,allocation=allocation).run(transport='stdio')
