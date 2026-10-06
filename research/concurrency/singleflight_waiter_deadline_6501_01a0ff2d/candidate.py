"""Actual asyncio deadlines; descriptive evidence only, no runtime adoption."""
import asyncio
import itertools
import time

POLICIES = ('direct', 'shield', 'shield_deadline')
SCHEDULES = ('fresh', 'preexpired', 'timeout', 'decision_delay', 'unknown')
WAIT_NS = 50_000_000

def deadline_valid(decision_ns, deadline_ns):
    return decision_ns < deadline_ns

async def condition(policy, schedule, suppress):
    events = []
    started = asyncio.Event()
    release = asyncio.Event()
    def emit(name, **fields):
        events.append({'seq': len(events), 'name': name, 'ns': time.perf_counter_ns(), **fields})
    async def producer():
        emit('producer_start')
        started.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            emit('producer_cancel', suppress=suppress)
            if not suppress:
                raise
            # Authored noncooperative cleanup, not a measured backend duration.
            await asyncio.sleep(0.1)
        result = 'UNKNOWN' if schedule == 'unknown' else 'READY'
        emit('producer_return', result=result)
        return result
    owner = asyncio.create_task(producer())
    await started.wait()
    async def companion():
        try:
            value = await owner
            emit('companion_return', result=value)
            return {'terminal': 'value', 'result': value, 'accepted': value == 'READY'}
        except asyncio.CancelledError:
            emit('companion_cancel')
            return {'terminal': 'cancelled', 'accepted': False}
    peer = asyncio.create_task(companion())
    await asyncio.sleep(0)
    now = time.perf_counter_ns()
    deadline = now - 1 if schedule == 'preexpired' else now + (WAIT_NS if schedule in ('timeout', 'decision_delay') else 1_000_000_000)
    emit('wait_start', deadline_ns=deadline)
    if schedule in ('fresh', 'decision_delay', 'unknown'):
        release.set()
    try:
        target = owner if policy == 'direct' else asyncio.shield(owner)
        value = await asyncio.wait_for(target, max(0, (deadline - time.perf_counter_ns()) / 1_000_000_000))
        emit('wait_return', result=value)
        if schedule == 'decision_delay':
            await asyncio.sleep(max(0, (deadline - time.perf_counter_ns()) / 1_000_000_000) + 0.04)
        decision_ns = time.perf_counter_ns()
        accepted = value == 'READY' and (policy != 'shield_deadline' or deadline_valid(decision_ns, deadline))
        timed = {'terminal': 'value', 'result': value, 'accepted': accepted, 'decision_ns': decision_ns}
    except TimeoutError:
        timed = {'terminal': 'timeout', 'accepted': False, 'decision_ns': time.perf_counter_ns()}
    emit('timed_decision', **timed)
    pending_before_cleanup = not owner.done()
    emit('cleanup_begin', pending_producer=pending_before_cleanup)
    release.set()
    await asyncio.gather(owner, peer, return_exceptions=True)
    emit('cleanup_end', producer_done=owner.done(), companion_done=peer.done())
    return {'policy': policy, 'schedule': schedule, 'suppress_cancel': suppress,
            'deadline_ns': deadline, 'timed': timed, 'companion': peer.result(),
            'pending_before_cleanup': pending_before_cleanup,
            'producer_cancelled': owner.cancelled(), 'all_tasks_terminal': owner.done() and peer.done(), 'events': events}

async def matrix():
    rows = []
    for policy, schedule, suppress in itertools.product(POLICIES, SCHEDULES, (False, True)):
        row = await condition(policy, schedule, suppress)
        row['id'] = f'{policy}/{schedule}/{int(suppress)}'
        rows.append(row)
    return rows
