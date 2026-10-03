"""Saved-only clock and launch-custody validation; imports no acquisition."""
import reference as ref

def check_snapshot(s):
    begin,end,cb,ce = [ref.integer(s[k]) for k in ('begin_ns','end_ns','cpu_read_begin_ns','cpu_read_end_ns')]
    ref.need(begin <= cb <= ce <= end, 'CPU read bracket chronology')
    cpu = {}
    for line in s['cpu_stat_raw'].splitlines():
        parts = line.split()
        ref.need(len(parts)==2 and parts[0] not in cpu and parts[1].isdigit(), 'unique CPU grammar')
        cpu[parts[0]] = int(parts[1])
    ref.need({'usage_usec','nr_periods','nr_throttled','throttled_usec'} <= set(cpu), 'required leaf CPU counters')
    for value in s['cpu_stat'].values(): ref.need(ref.integer(value)>=0,'nonnegative exact CPU')
    ref.join(s['cpu_stat'],cpu,'raw CPU typed join')
    for k in ('process_cpu_ns','thread_cpu_ns','voluntary','involuntary'):
        ref.need(ref.integer(s[k])>=0,'process counter')
    return cpu

def check_trace(t, paint_start, paint_end):
    due = ref.integer(t['due_ns'])
    start,end = ref.integer(paint_start),ref.integer(paint_end)
    pre,post,w = t['pre'],t['post'],t['wait']
    before,after = check_snapshot(pre),check_snapshot(post)
    begin,returned = ref.integer(w['begin_ns']),ref.integer(w['return_ns'])
    ref.need(pre['end_ns'] <= begin <= returned <= post['begin_ns'] <= post['end_ns'] <= start <= end,
             'source/observer wait-snapshot-native chronology')
    ref.need(due<=returned,'wait returned before deadline')
    ref.need(set(before)==set(after),'stable CPU counter schema')
    for k in before: ref.need(after[k]>=before[k],'CPU counter regression')
    for k in ('process_cpu_ns','thread_cpu_ns','voluntary','involuntary'):
        ref.need(post[k]>=pre[k],'process counter regression')
    last,overshoots,past_due = begin,[],False
    for sl in w['sleeps']:
        ss,sr,requested = [ref.integer(sl[k]) for k in ('start_ns','return_ns','requested_ns')]
        ref.need(last==ss<=sr<=returned and requested>0 and requested==due-ss-15_000_000,
                 'complete coarse-sleep geometry')
        ref.need(sr-ss>=requested,'coarse sleep duration')
        overshoots.append(sr-ss-requested)
        past_due = past_due or sr>due
        last = sr
    spin=w['spin_enter_ns']
    if spin is not None:
        ref.need(last==ref.integer(spin)<due and 0<due-spin<=15_000_000 and spin<=returned,'final-spin grammar')
    else:
        ref.need(returned==last and (begin>=due or (w['sleeps'] and last>=due)),'exact no-spin final sample')
    return {'wait_lateness_ns':returned-due,'post_wait_to_native_ns':start-returned,
            'nr_throttled_delta':after['nr_throttled']-before['nr_throttled'],
            'coarse_past_due':bool(past_due),'sleep_overshoot_ns':overshoots}

def admit_launch(receipt, freeze):
    try:
        ref.need(ref.integer(receipt['exit_code'])==0 and ref.integer(receipt['inspect_exit'])==0,
                 'actual producer terminal0')
        ref.join(receipt['command'],freeze['producer_command'],'frozen launch command')
        state=ref.parse_record(receipt['inspect_stdout'])
        ref.need(state['State']['Status']=='exited' and ref.integer(state['State']['ExitCode'])==0,
                 'inspected producer exited0')
        for k in ('Running','Paused','Restarting','OOMKilled','Dead'):
            ref.need(state['State'][k] is False,'inspected terminal state '+k)
        ref.need(ref.integer(state['RestartCount'])==0,'restart0')
        ref.need(state['Image']==freeze['image_id'],'inspected image')
        ref.need(state['Config']['User']=='501:501','nonroot identity')
        ref.join(state['Config']['Cmd'],freeze['native_argv'],'native argv')
        h=state['HostConfig']
        ref.join({'Entrypoint':state['Config']['Entrypoint'],**{k:h[k] for k in ('Runtime','Privileged','CapAdd','Tmpfs')}},
                 freeze['effective_runtime'],'effective runtime/isolation')
        ref.join({k:h[k] for k in ('NanoCpus','Memory','MemorySwap','PidsLimit','NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt')},
                 {'NanoCpus':1000000000,'Memory':536870912,'MemorySwap':536870912,'PidsLimit':64,
                  'NetworkMode':'none','ReadonlyRootfs':True,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges']},
                 'inspected limits/isolation')
        ref.join([(m['Source'],m['Destination'],m['RW']) for m in state['Mounts']],
                 [(freeze['guest_source'],'/src',False),(freeze['guest_output'],'/out',True)],'source/output mounts')
        return state
    except (KeyError,TypeError) as exc:
        raise ValueError('incomplete launch custody') from exc

def check_continuity(previous, current, previous_native_end):
    post,pre=previous['post'],current['pre']
    check_snapshot(post); check_snapshot(pre)
    ref.need(ref.integer(previous_native_end)<=pre['begin_ns'],'stream native/snapshot continuity')
    for k in ('process_cpu_ns','thread_cpu_ns','voluntary','involuntary'):
        ref.need(pre[k]>=post[k],'cross-wait process counter regression')

def check_shared_cpu(snapshots):
    checked=[(s,check_snapshot(s)) for s in snapshots]
    for first,a in checked:
        for second,b in checked:
            if first is second: continue
            if first['cpu_read_end_ns']<=second['cpu_read_begin_ns']:
                ref.need(set(a)==set(b),'shared CPU schema')
                for k in a: ref.need(b[k]>=a[k],'disjoint shared CPU read regression')

def admit_transport(consumed, launch, copied, after, freeze):
    try:
        ref.need(consumed['mode']=='source-boundary-diagnostic','consumed diagnostic mode')
        before,idle=consumed['readiness']['guest_sha256'],consumed['readiness']['idle']
        sequence=[(before,'hash_command'),(idle,'idle_command')]
        last=0
        for receipt,key in sequence:
            ref.join(receipt['command'],freeze[key],'frozen '+key)
            ref.need(ref.integer(receipt['exit_code'])==0,'preflight exit0')
            start,end=ref.integer(receipt['started_ns']),ref.integer(receipt['finished_ns'])
            ref.need(last<=start<=end,'host preflight clock chronology'); last=end
        ref.need(not idle['stdout'].strip(),'private engine idle receipt')
        mark=ref.integer(consumed['started_ns'])
        ref.need(last<=mark,'host consumed chronology'); last=mark
        steps=[(consumed['mkdir'],'mkdir_command'),(launch,None),(launch['inspection'],'inspect_command'),
               (copied,'copy_command'),(after,'hash_command')]
        for actual,recorded in (('inspect_exit','exit_code'),('inspect_stdout','stdout'),('inspect_stderr','stderr')):
            ref.join(launch[actual],launch['inspection'][recorded],'inspection receipt alias')
        for receipt,key in steps:
            if key is not None:
                ref.join(receipt['command'],freeze[key],'frozen '+key)
                ref.need(ref.integer(receipt['exit_code'])==0,'transport exit0')
            start,end=ref.integer(receipt['started_ns']),ref.integer(receipt['finished_ns'])
            ref.need(last<=start<=end,'host transport clock chronology'); last=end
        ref.need(before['stdout']==after['stdout'],'pre/post staged source bytes')
    except (KeyError,TypeError) as exc:
        raise ValueError('incomplete transport custody') from exc
