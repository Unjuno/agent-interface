"""Experimental orchestration core; no WSLc driver or production guarantees."""
import json
import math
from pathlib import Path
import time


def run_attempt(allocation, conditions, driver, *, timeout_s):
    if not isinstance(conditions, dict) or not conditions.get('run_id'):
        raise ValueError('conditions require a run_id')
    if type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError('positive finite timeout required')
    frozen = json.dumps(conditions, sort_keys=True, indent=2) + '\n'
    allocation = Path(allocation)
    allocation.mkdir(parents=False, exist_ok=False)
    started = time.monotonic_ns()
    deadline_ns = started + int(timeout_s * 1_000_000_000)
    (allocation / 'conditions.json').write_text(frozen, encoding='utf-8')
    events = {'started_ns': started, 'conditions_written_ns': time.monotonic_ns()}
    host = container = None
    host_attempted = container_attempted = False
    container_result = {'status':'not_started','exit_code':None}
    host_result = {'status':'not_started','exit_code':None}
    cleanup = {'status':'not_started'}
    audit = {'status':'not_run'}
    error = None
    fatal = None
    cleanup_errors = []
    phase = 'prepare'
    try:
        # Preparation must only allocate local identity tokens, never start a resource.
        host = driver.prepare_host(allocation)
        container = driver.prepare_container(allocation)
        phase = 'host_start'; host_attempted = True
        driver.start_host(host, allocation); events['host_started_ns'] = time.monotonic_ns()
        phase = 'before_container_start'
        container_start_timeout = (deadline_ns - time.monotonic_ns()) / 1_000_000_000
        if container_start_timeout <= 0: raise TimeoutError('execution deadline before container start')
        phase = 'container_start'; container_attempted = True
        driver.start_container(container, allocation, container_start_timeout)
        events['container_started_ns'] = time.monotonic_ns()
        phase = 'container_wait'
        remaining = max(0.0, (deadline_ns - time.monotonic_ns()) / 1_000_000_000)
        if remaining <= 0: raise TimeoutError('execution deadline before container wait')
        container_result = driver.wait_container(container, remaining)
        if not isinstance(container_result, dict):
            container_result = {'status':'unknown','exit_code':None}
            raise TypeError('invalid container receipt')
        events['container_wait_returned_ns'] = time.monotonic_ns()
        if events['container_wait_returned_ns'] >= deadline_ns:
            raise TimeoutError('execution deadline elapsed before container wait returned')
    except BaseException as exc:
        error = {'phase':phase,'type':type(exc).__name__}
        if not isinstance(exc, Exception): fatal = exc
        if phase == 'host_start': host_result = {'status':'unknown','exit_code':None}
        if phase in ('container_start','container_wait') and not isinstance(container_result, dict):
            container_result = {'status':'unknown','exit_code':None}
        if phase == 'container_start' or (phase == 'container_wait' and container_result.get('status') == 'not_started'):
            container_result = {'status':'unknown','exit_code':None}
    finally:
        # A separate shared cleanup budget remains even after execution expiry.
        cleanup_deadline_ns = time.monotonic_ns() + int(timeout_s * 1_000_000_000)
        if host_attempted:
            try: host_result = driver.stop_host(host, max(0.0, (cleanup_deadline_ns-time.monotonic_ns()) / 1_000_000_000))
            except BaseException as exc:
                host_result = {'status':'unknown','error_type':type(exc).__name__}
                cleanup_errors.append({'phase':'host_cleanup','type':type(exc).__name__})
                if fatal is None and not isinstance(exc, Exception): fatal = exc
        if not isinstance(host_result, dict):
            host_result = {'status':'unknown','error_type':'InvalidReceipt'}
            cleanup_errors.append({'phase':'host_cleanup','type':'InvalidReceipt'})
        events['host_cleanup_returned_ns'] = time.monotonic_ns()
        if container_attempted:
            try: cleanup = driver.cleanup_container(container, max(0.0, (cleanup_deadline_ns-time.monotonic_ns()) / 1_000_000_000))
            except BaseException as exc:
                cleanup = {'status':'unknown','error_type':type(exc).__name__}
                cleanup_errors.append({'phase':'container_cleanup','type':type(exc).__name__})
                if fatal is None and not isinstance(exc, Exception): fatal = exc
        if not isinstance(cleanup, dict):
            cleanup = {'status':'unknown','error_type':'InvalidReceipt'}
            cleanup_errors.append({'phase':'container_cleanup','type':'InvalidReceipt'})
        events['container_cleanup_returned_ns'] = time.monotonic_ns()
        cleanup_deadline_exceeded = events['container_cleanup_returned_ns'] >= cleanup_deadline_ns
    # This is only eligible for scoring after the producer exited successfully.
    # The driver must ensure artifacts are stable before returning a score.
    if fatal is None and container_result.get('status') == 'exited' and container_result.get('exit_code') == 0:
        try: audit = driver.audit(allocation)
        except BaseException as exc:
            audit = {'status':'error','error_type':type(exc).__name__}
            if fatal is None and not isinstance(exc, Exception): fatal = exc
    if not isinstance(audit, dict): audit = {'status':'error','error_type':'InvalidReceipt'}
    events['before_result_write_ns'] = time.monotonic_ns()
    release = 'confirmed' if audit.get('release_confirmed') is True else 'UNKNOWN'
    eligible = (error is None and fatal is None and not cleanup_deadline_exceeded and container_result.get('status') == 'exited'
                and container_result.get('exit_code') == 0
                and host_result.get('status') == 'exited' and host_result.get('exit_code') == 0
                and cleanup.get('status') == 'confirmed' and audit.get('status') == 'passed'
                and release == 'confirmed')
    result = {'status':'completed_scoped' if eligible else 'incomplete',
              'input_release':release,'container':container_result,'host':host_result,
              'cleanup':cleanup,'cleanup_deadline_exceeded':cleanup_deadline_exceeded,
              'audit':audit,'error':error,'cleanup_errors':cleanup_errors,'events':events}
    tmp = allocation / 'result.tmp'
    tmp.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    tmp.replace(allocation / 'result.json')
    if fatal is not None: raise fatal
    return result
