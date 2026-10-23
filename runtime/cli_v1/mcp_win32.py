"""Synthetic-only public MCP surface for the guarded Win32 owner seam."""
import asyncio
from pydantic import Field, StrictInt, StrictStr
from typing import Annotated
import uuid

from mcp.types import CallToolResult


_START_RESPONSE_HANDOFF_NS = 50_000_000


def register_guarded_win32_tools(server, owner, content, *, producer_factory,
                                task_oracle=None):
    """Expose only admission and cancellation custody; never native input.

    The injected owner derives target generation from its configured target.
    The public caller cannot supply or replace that digest. Producer and task
    oracle callbacks are injected and must remain synthetic in this route.
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
        replay. This route has no native-input producer. Task effect is scored
        only by the separate optional independent-oracle tool.
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

    if callable(task_oracle):
        @server.tool()
        async def interface_guarded_win32_verify_task(
                call_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')],
                wait_for_result_ms: Annotated[StrictInt, Field(ge=0, le=10000)] = 2000
                ) -> CallToolResult:
            """Ask a separate injected oracle to score this action's task effect.

            This is distinct from producer completion, cancellation recovery,
            and neutral-input readback. The receipt is one-use and bound to the
            action's call, operation and target generation. Unknown or timed-out
            oracle results remain unknown; they cannot be replaced or replayed.
            Observation timestamps must use this host's monotonic clock and
            lie between oracle reservation and receipt processing. This time
            check does not authenticate the external evidence or prove causality.
            """
            try:
                reserved = owner.begin_task_effect_verification(call_id)
            except ValueError:
                return content({'status': 'unknown_call', 'call_id': call_id,
                    'operation_invoked': False, 'task_success': None,
                    'replay_allowed': False}, error=True)
            if not reserved:
                existing = owner.interface_result(call_id)
                if existing is None:
                    return content({'status': 'unknown_call', 'call_id': call_id,
                        'operation_invoked': False, 'task_success': None,
                        'replay_allowed': False}, error=True)
                effect = existing.get('task_effect')
                if not isinstance(effect, dict):
                    effect = {'status': 'unknown', 'task_success': None}
                return content({'status': effect.get('status', 'unknown'),
                    'call_id': call_id, 'task_effect': effect,
                    'task_success': effect.get('task_success'),
                    'operation_invoked': False, 'input_dispatched': False,
                    'replay_allowed': False, 'scope': 'synthetic_only'})

            existing = owner.interface_result(call_id)
            if existing is None:
                row = owner.fail_task_effect_verification(
                    call_id, 'action_disappeared_after_oracle_reservation')
                return content({'status': 'unknown', 'call_id': call_id,
                    'task_effect': row['task_effect'], 'task_success': None,
                    'operation_invoked': False, 'input_dispatched': False,
                    'replay_allowed': False, 'scope': 'synthetic_only'}, error=True)
            action = existing['action']
            task = asyncio.create_task(asyncio.to_thread(task_oracle,
                {'call_id': call_id, **action}))
            task_oracle_tasks.add(task)

            def oracle_finished(done):
                task_oracle_tasks.discard(done)
                if not done.cancelled():
                    done.exception()

            task.add_done_callback(oracle_finished)
            done, _ = await asyncio.wait({task},
                timeout=max(0, wait_for_result_ms * 1_000_000
                            - _START_RESPONSE_HANDOFF_NS) / 1_000_000_000)
            if not done:
                row = owner.fail_task_effect_verification(
                    call_id, 'independent_task_oracle_response_timeout')
            else:
                try:
                    receipt = task.result()
                    row = owner.record_task_effect(call_id, receipt)
                except Exception as error:
                    row = owner.fail_task_effect_verification(
                        call_id, 'independent_task_oracle_receipt_invalid: ' + repr(error))
            effect = row['task_effect']
            return content({'status': effect['status'], 'call_id': call_id,
                'task_effect': effect, 'task_success': effect['task_success'],
                'operation_invoked': False, 'input_dispatched': False,
                'replay_allowed': False, 'scope': 'synthetic_only'},
                error=effect['status'] == 'unknown')

        task_oracle_tasks = set()

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
