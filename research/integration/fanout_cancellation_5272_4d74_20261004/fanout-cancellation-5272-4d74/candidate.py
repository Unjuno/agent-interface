import asyncio,json,pathlib,time,platform
R=pathlib.Path(__file__).resolve().parent
P=json.loads((R/'PLAN.json').read_text());rows=[]
async def cell(case,policy):
    events=[];start=time.monotonic_ns();ready=asyncio.Event();finish=asyncio.Event();live=set();released=False
    def log(kind,**kw):events.append(dict(event=kind,t_ns=time.monotonic_ns()-start,live=sorted(live),**kw))
    async def worker():
        nonlocal released
        live.add('original');log('worker_start');ready.set()
        try:
            if case=='completion_race':await finish.wait()
            else:await asyncio.sleep(1)
        except asyncio.CancelledError:
            log('cancel_observed')
            if case in ('slow_cleanup','suppressed_late','mandatory_unfinished'):await asyncio.sleep(P['cleanup_seconds'])
            if case=='suppressed_late':log('late_result',result='PASS')
        finally:
            if case!='missing_release':released=True;log('release_receipt')
            live.remove('original');log('worker_terminal')
        return 'PASS'
    async def replacement():
        live.add('replacement');log('replacement_start');await asyncio.sleep(P['ordinary_work_seconds']);live.remove('replacement');log('replacement_terminal')
    task=asyncio.create_task(worker());await ready.wait()
    if case=='completion_race':finish.set();await task
    decision='UNKNOWN' if case=='mandatory_unfinished' else 'FAIL';log('decision_sealed',decision=decision)
    if not task.done():task.cancel();log('cancel_requested')
    replacement_task=None
    if policy=='REQUEST_ONLY':
        log('slot_refunded',basis='cancel_request_or_done');replacement_task=asyncio.create_task(replacement());await asyncio.sleep(0)
    await task
    log('task_joined',done=task.done())
    if policy=='TERMINAL_RELEASE' and released:
        log('slot_refunded',basis='terminal_and_release');replacement_task=asyncio.create_task(replacement())
    elif policy=='TERMINAL_RELEASE':log('slot_hold',reason='release_unavailable')
    if replacement_task:await replacement_task
    log('cell_terminal',decision=decision)
    return dict(case=case,policy=policy,events=events,decision=decision,release_observed=released,peak_live=max(len(e['live']) for e in events))
async def main():
    for case in P['cases']:
        for policy in P['policies']:rows.append(await cell(case,policy))
asyncio.run(main())
cgroups={}
for n in ['cpu.max','memory.max','pids.max']:
    p=pathlib.Path('/sys/fs/cgroup')/n;cgroups[n]=p.read_text().strip() if p.exists() else None
print(json.dumps(dict(rows=rows,python=platform.python_version(),cgroups=cgroups,scope='real asyncio coroutines, logical fixture release only; no backend resource certificate'),indent=2))
