"""Development-only dual-lifetime executor candidate.

Only scheduled owner-deadline expiry receives a bounded passive observation
lifecycle after verified input release. No program tail resumes and no new
input lease/authority is created. Cancellation/focus/surface failures retain
their existing terminal classes.
"""
from __future__ import annotations
import time
from executor_v12 import Executor as Previous
from lease import Expired
from executor_v3 import Cancelled, DecisionRequired

POST_AUTHORITY_BUDGET_NS = 400_000_000

class Executor(Previous):
    def _run(self, identifier, steps, lease):
        status = 'completed'
        error = None
        completed = 0
        decision_reason = None
        scheduled_authority_end = False
        post = None
        try:
            for index, step in enumerate(steps):
                if lease.is_set():
                    raise Cancelled()
                self.emit(dict(event='step_started', id=identifier, step=index,
                               operation=step['op'], issued_ns=time.perf_counter_ns()))
                self.backend.execute(step, lease, identifier, index)
                if lease.is_set():
                    raise Cancelled()
                completed += 1
                self.emit(dict(event='step_completed', id=identifier, step=index,
                               completed_ns=time.perf_counter_ns()))
        except Expired:
            scheduled_authority_end = True
            status = 'authority_ended'
        except DecisionRequired as exc:
            status = 'needs_decision'
            decision_reason = str(exc) or None
        except Cancelled:
            status = 'cancelled'
        except Exception as exc:
            status = 'failed'
            error = repr(exc)
        finally:
            try:
                release = self.backend.release_all()
                if release.get('verified') is not True:
                    status = 'failed'
                    error = 'input release not verified'
            except Exception as exc:
                release = dict(verified=False, error=repr(exc))
                status = 'failed'
                error = repr(exc)

            interruption = lease.interruption_snapshot()
            if status == 'completed':
                try:
                    if lease.is_set():
                        raise Cancelled()
                except Expired:
                    scheduled_authority_end = True
                    status = 'authority_ended'
                except DecisionRequired as exc:
                    status = 'needs_decision'
                    decision_reason = str(exc) or None
                except Cancelled:
                    status = 'cancelled'

            reason = None
            if isinstance(interruption, dict) and isinstance(interruption.get('record'), dict):
                reason = interruption['record'].get('reason')
            eligible = (scheduled_authority_end and status == 'authority_ended'
                        and reason == 'expired' and release.get('verified') is True)

            if eligible:
                lifecycle_started_ns = time.perf_counter_ns()
                lifecycle_deadline_ns = lifecycle_started_ns + POST_AUTHORITY_BUDGET_NS
                self.emit(dict(event='authority_ended', id=identifier,
                               cause='scheduled_deadline', release=release,
                               interruption=interruption,
                               authority_ended_ns=lifecycle_started_ns,
                               lifecycle_deadline_ns=lifecycle_deadline_ns,
                               grants_input_authority=False,
                               tail_program_steps_resumed=0,
                               allowed_followup='one passive snapshot only'))
                post = dict(captures=0, sequence=None, error=None,
                            lifecycle_deadline_ns=lifecycle_deadline_ns,
                            grants_input_authority=False,
                            tail_program_steps_resumed=0)
                try:
                    if time.perf_counter_ns() >= lifecycle_deadline_ns:
                        post['error'] = 'lifecycle deadline exhausted before snapshot'
                    else:
                        before_sequence = self.backend.sequence
                        self.backend.snapshot(identifier, completed)
                        post['captures'] = 1
                        post['sequence'] = self.backend.sequence
                        post['sequence_advanced'] = self.backend.sequence == before_sequence + 1
                        post['snapshot_finished_ns'] = time.perf_counter_ns()
                        post['within_lifecycle_deadline'] = post['snapshot_finished_ns'] <= lifecycle_deadline_ns
                except Exception as exc:
                    post['error'] = repr(exc)
                    post['snapshot_finished_ns'] = time.perf_counter_ns()
                    post['within_lifecycle_deadline'] = post['snapshot_finished_ns'] <= lifecycle_deadline_ns

            with self.lock:
                self.emit(dict(event='terminal', id=identifier, status=status, error=error,
                               steps_completed=completed, release=release,
                               interruption=interruption, decision_reason=decision_reason,
                               post_authority_observation=post,
                               terminal_ns=time.perf_counter_ns(),
                               semantic_completion='program status only; task scoring is separate'))
                self.active = None
