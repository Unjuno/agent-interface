"""Synthetic-only public MCP surface for the guarded Win32 owner seam."""
import asyncio
from pydantic import Field, StrictInt, StrictStr
from typing import Annotated
import uuid

from mcp.types import CallToolResult


_START_RESPONSE_HANDOFF_NS = 50_000_000


def register_guarded_win32_tools(server, owner, content, *, producer_factory):
    """Expose only admission and cancellation custody; never native input.

    The injected owner must derive target generation from its configured
    Windows target. The public caller cannot supply or replace that digest.
    This surface does not launch a producer and cannot report task success.
    """
    @server.tool()
    async def interface_guarded_win32_bind_target() -> CallToolResult:
        """Read and pin the configured target generation before a caller wait.

        This is identity metadata only, not a pixel observation, application
        readiness signal or task oracle. The single-use token expires on use;
        admission re-reads the configured target and refuses a changed generation.
        """
        try:
            return content(owner.bind_target_generation())
        except (RuntimeError, ValueError) as error:
            return content({'status': 'unknown',
                'error': 'TARGET_BINDING_UNAVAILABLE', 'detail': repr(error),
                'operation_invoked': False, 'input_dispatched': False,
                'task_success': None, 'replay_allowed': False}, error=True)

    @server.tool()
    async def interface_guarded_win32_admit(
            action_operation_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')],
            target_binding_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')],
            operation_deadline_ns: StrictInt,
            obligations: list[StrictStr]) -> CallToolResult:
        """Freeze one synthetic operation's target generation and obligations.

        This admission-only step sends no input and starts no producer. The
        target generation comes from the injected owner, never this request.
        A returned call ID is stable for result retrieval; do not replay it.
        """
        call_id = uuid.uuid4().hex
        try:
            row = owner.admit_action_from_binding(call_id, action_operation_id,
                target_binding_id, operation_deadline_ns=operation_deadline_ns,
                obligations=obligations,
                action_metadata={'source': 'synthetic_public_mcp_admission'})
        except RuntimeError as error:
            if str(error) == 'TARGET_GENERATION_CHANGED':
                return content({'status': 'invalid_request',
                    'error': 'TARGET_GENERATION_CHANGED',
                    'operation_invoked': False, 'input_dispatched': False,
                    'task_success': None, 'replay_allowed': False}, error=True)
            return content({'status': 'invalid_request', 'error': repr(error),
                'operation_invoked': False, 'input_dispatched': False,
                'task_success': None, 'replay_allowed': False}, error=True)
        except ValueError as error:
            return content({'status': 'invalid_request', 'error': repr(error),
                'operation_invoked': False, 'input_dispatched': False,
                'task_success': None, 'replay_allowed': False}, error=True)
        row.update(status=row.get('action', {}).get('status', 'unknown'),
                   operation_invoked=False, input_dispatched=False,
                   task_success=None, replay_allowed=False,
                   scope='synthetic_only')
        return content(row)

    @server.tool()
    async def interface_guarded_win32_start(
            call_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')],
            wait_for_result_ms: Annotated[StrictInt, Field(ge=0, le=10000)] = 0
            ) -> CallToolResult:
        """Start the already-admitted synthetic child behind its parent gate.

        The injected factory must return an inert child waiting on its start
        gate. A pending reply names the original action; it does not authorize
        replay. This route has no native-input producer or task-effect claim.
        """
        task = asyncio.create_task(asyncio.to_thread(
            owner.start_producer, call_id, producer_factory))
        start_tasks.add(task)

        def finished(done):
            start_tasks.discard(done)
            if not done.cancelled():
                done.exception()

        task.add_done_callback(finished)
        done, _ = await asyncio.wait({task},
            timeout=max(0, wait_for_result_ms * 1_000_000
                        - _START_RESPONSE_HANDOFF_NS) / 1_000_000_000)
        if not done:
            return content({'status': 'pending', 'call_id': call_id,
                'result_available': True, 'operation_invoked': True,
                'input_dispatched': False, 'release_confirmed': False,
                'task_success': None, 'replay_allowed': False,
                'scope': 'synthetic_only'})
        try:
            row = task.result()
        except Exception as error:
            return content({'status': 'unknown', 'call_id': call_id,
                'error': repr(error), 'operation_invoked': True,
                'input_dispatched': False, 'release_confirmed': False,
                'task_success': None, 'replay_allowed': False,
                'scope': 'synthetic_only'}, error=True)
        row.update(status=row.get('action', {}).get('status', 'unknown'),
            operation_invoked=True, input_dispatched=False,
            release_confirmed=False, task_success=None, replay_allowed=False,
            scope='synthetic_only')
        return content(row)

    start_tasks = set()

    @server.tool()
    async def interface_guarded_win32_cancel(
            call_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')],
            cleanup_deadline_ns: StrictInt) -> CallToolResult:
        """Close admission and request the owner's bounded synthetic recovery.

        The response is only a custody receipt. UNKNOWN remains non-replayable;
        recovery confirmation is not task success or native Windows release.
        """
        result = owner.cancel_guarded(call_id,
            cleanup_deadline_ns=cleanup_deadline_ns)
        result.update(input_dispatched=False, task_success=None,
                      replay_allowed=False, scope='synthetic_only')
        return content(result)
