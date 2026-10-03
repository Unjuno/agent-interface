"""Actual asyncio Task cancellation; controlled event barriers, no GUI or authority."""
import argparse
import asyncio
import hashlib
import json
import platform
import sys
from pathlib import Path

POLICIES = ('independent', 'direct', 'shield', 'shield_refcount')
SCENARIOS = ('stable', 'cancel_first', 'cancel_last', 'cancel_all', 'generation_change', 'owner_failure')
PAYLOAD = hashlib.sha256(b'descriptive-read:surface-A:generation-1').hexdigest()

async def run_case(policy, scenario, callers):
    events = []
    gate = asyncio.Event()
    producer_ready = []
    waiter_ready = [asyncio.Event() for _ in range(callers)]
    current_generation = 1
    remaining = callers

    def emit(actor, kind, **fields):
        events.append(dict(seq=len(events)+1, actor=actor, kind=kind, **fields))

    async def producer(index, ready):
        actor = 'p'+str(index)
        emit(actor, 'producer_start')
        ready.set()
        try:
            await gate.wait()
            if scenario == 'owner_failure':
                emit(actor, 'producer_error', error='RuntimeError')
                raise RuntimeError('read-only owner failed')
            result = dict(generation=1, payload_sha256=PAYLOAD)
            emit(actor, 'producer_return', **result)
            return result
        except asyncio.CancelledError:
            emit(actor, 'producer_cancelled')
            raise
        finally:
            emit(actor, 'producer_exit')

    count = callers if policy == 'independent' else 1
    producers = []
    for index in range(count):
        ready = asyncio.Event()
        producer_ready.append(ready)
        producers.append(asyncio.create_task(producer(index, ready)))

    async def waiter(index):
        nonlocal remaining
        actor = 'w'+str(index)
        task = producers[index if policy == 'independent' else 0]
        emit(actor, 'waiter_start')
        waiter_ready[index].set()
        try:
            result = await (asyncio.shield(task) if policy.startswith('shield') else task)
            # Descriptive read result is checked separately for this caller.
            status = 'DELIVERED' if result['generation'] == current_generation else 'STALE'
            emit(actor, 'waiter_result', status=status, current_generation=current_generation, **result)
            return dict(caller=index, status=status, generation=result['generation'], payload_sha256=result['payload_sha256'])
        except asyncio.CancelledError:
            emit(actor, 'waiter_cancelled')
            return dict(caller=index, status='CANCELLED', generation=None, payload_sha256=None)
        except RuntimeError:
            emit(actor, 'waiter_error', error='RuntimeError')
            return dict(caller=index, status='OWNER_FAILED', generation=None, payload_sha256=None)
        finally:
            remaining -= 1
            emit(actor, 'waiter_detach', remaining=remaining)
            if policy == 'shield_refcount' and remaining == 0 and not task.done():
                emit('coordinator', 'last_waiter_cancel', producer='p0')
                task.cancel()

    waiters = [asyncio.create_task(waiter(index)) for index in range(callers)]
    await asyncio.gather(*(event.wait() for event in producer_ready+waiter_ready))
    emit('coordinator', 'barrier_ready')
    cancel = ([0] if scenario == 'cancel_first' else [callers-1] if scenario == 'cancel_last'
              else list(range(callers)) if scenario == 'cancel_all' else [])
    for index in cancel:
        emit('coordinator', 'cancel_request', caller=index)
        waiters[index].cancel()
    if cancel:
        await asyncio.gather(*(waiters[index] for index in cancel))
    if scenario == 'generation_change':
        current_generation = 2
        emit('coordinator', 'generation_change', generation=2)
    if scenario != 'cancel_all':
        emit('coordinator', 'gate_open')
        gate.set()
    outcomes = await asyncio.gather(*waiters)
    # Let cancellation finalizers run before observing producer ownership.
    await asyncio.sleep(0)
    before = [dict(producer='p'+str(i), done=p.done(), cancelled=p.cancelled()) for i,p in enumerate(producers)]
    for index,task in enumerate(producers):
        if not task.done():
            emit('coordinator', 'cleanup_cancel', producer='p'+str(index))
            task.cancel()
    await asyncio.gather(*producers, return_exceptions=True)
    after = [dict(producer='p'+str(i), done=p.done(), cancelled=p.cancelled()) for i,p in enumerate(producers)]
    return dict(policy=policy, scenario=scenario, callers=callers, events=events,
                outcomes=outcomes, before_cleanup=before, after_cleanup=after)

async def matrix():
    rows=[]
    for callers in (2,3):
        for scenario in SCENARIOS:
            for policy in POLICIES:
                rows.append(await asyncio.wait_for(run_case(policy,scenario,callers), timeout=2))
    return rows, type(asyncio.get_running_loop()).__name__

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    rows, loop_type = asyncio.run(matrix())
    result=dict(schema='asyncio-singleflight-cancellation-v1', python=sys.version,
                platform=platform.platform(), event_loop=loop_type, rows=rows)
    with Path(args.output).open('x',encoding='utf-8',newline='\n') as out:
        json.dump(result,out,indent=2,sort_keys=True)
        out.write('\n')
    print(json.dumps({'rows':len(result['rows']),'output':args.output}))

if __name__=='__main__':
    main()
