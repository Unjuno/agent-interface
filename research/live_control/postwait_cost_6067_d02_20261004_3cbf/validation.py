"""Collection integrity only; exposure/deadline failures are retained outcomes."""
import base64
import hashlib
import json
import struct

def ordered(*values):
    if any(type(v) is not int or v < 0 for v in values) or list(values) != sorted(values):
        raise ValueError('typed monotonic clock bracket required')

def snapshot_valid(s):
    ordered(s['begin_ns'],s['cpu_read_begin_ns'],s['cpu_read_end_ns'],s['end_ns'])
    parsed={}
    for line in s['cpu_stat_raw'].splitlines():
        parts=line.split()
        if len(parts)!=2 or parts[0] in parsed or not parts[1].isdigit():
            raise ValueError('unique leaf CPU counters')
        parsed[parts[0]]=int(parts[1])
    if parsed!=s['cpu_stat'] or any(type(v) is not int or v<0 for v in s['cpu_stat'].values()):
        raise ValueError('CPU raw/parsed identity')
    if not {'usage_usec','nr_periods','nr_throttled','throttled_usec'} <= parsed.keys():
        raise ValueError('required CPU counters')
    for name in ('process_cpu_ns','thread_cpu_ns','voluntary','involuntary'):
        if type(s[name]) is not int or s[name]<0: raise ValueError('typed CPU/context fields')
    for name in ('cpu_stat_local','schedstat','schedstats_enabled'):
        optional=s[name]
        if set(optional)!={'available','raw','error'} or type(optional['available']) is not bool:
            raise ValueError('explicit optional telemetry boundary')
        if optional['available']:
            if not isinstance(optional['raw'],str) or optional['error'] is not None:
                raise ValueError('available telemetry raw/type')
            if name=='schedstat':
                parts=optional['raw'].split()
                if len(parts)!=3 or any(not x.isdigit() for x in parts): raise ValueError('schedstat triplet')
            elif name=='schedstats_enabled':
                if optional['raw'].strip() not in ('0','1'): raise ValueError('schedstats enable flag')
            else:
                lines=[x.split() for x in optional['raw'].splitlines()]
                if (any(len(x)!=2 or not x[1].isdigit() for x in lines) or
                    len({x[0] for x in lines})!=len(lines) or 'throttled_usec' not in {x[0] for x in lines}):
                    raise ValueError('local CPU counter map')
        elif (optional['raw'] is not None or not isinstance(optional['error'],dict) or
              type(optional['error'].get('errno')) is not int or
              not isinstance(optional['error'].get('message'),str)):
            raise ValueError('unavailable telemetry error retained')

def wait_valid(w, due):
    pre,wait,post=w['pre'],w['wait'],w['post']
    if type(w['due_ns']) is not int or w['due_ns']!=due:
        raise ValueError('wait deadline join')
    snapshot_valid(pre)
    ordered(pre['end_ns'],wait['begin_ns'],wait['return_ns'])
    if wait['return_ns']<due: raise ValueError('early wait return')
    previous=wait['begin_ns']
    for sleep in wait['sleeps']:
        ordered(previous,sleep['start_ns'],sleep['return_ns'],wait['return_ns'])
        if type(sleep['requested_ns']) is not int or sleep['requested_ns']<=0:
            raise ValueError('positive sleep request')
        previous=sleep['return_ns']
    if wait['spin_enter_ns'] is not None:
        ordered(previous,wait['spin_enter_ns'],wait['return_ns'])
    if post is not None:
        snapshot_valid(post)
        ordered(wait['return_ns'],post['begin_ns'],post['end_ns'],w['paint_start_ns'])
    ordered(wait['return_ns'],w['paint_start_ns'],w['paint_end_ns'])

def validate_event(event,draw,clear,treatment):
    if treatment not in ('full','minimal') or type(event['id']) is not int or event['id'] not in range(1,9):
        raise ValueError('event identity and treatment')
    for kind,w in [('draw',draw),('clear',clear)]:
        if w['kind']!=kind or type(w['id']) is not int or w['id']!=event['id']:
            raise ValueError('source typed stream join')
        wait_valid(w,event['onset_ns'] if kind=='draw' else event['due_clear_ns'])
        if (w['paint_start_ns']!=event[kind+'_start_ns'] or
                w['paint_end_ns']!=event[kind+'_end_ns']):
            raise ValueError('paint record join')
    ordered(event['draw_start_ns'],event['draw_end_ns'],clear['pre']['begin_ns'],
            event['clear_start_ns'],event['clear_end_ns'])
    if (draw['post'] is None)!=(treatment=='minimal') or clear['post'] is None or clear['trial'] is not None:
        raise ValueError('exact draw-only treatment placement')
    t=draw['trial']; ordered(draw['wait']['return_ns'],t['begin_ns'],t['end_ns'],event['draw_start_ns'])
    wall=t['end_ns']-t['begin_ns']
    for cpu in ('process','thread'):
        ordered(t[cpu+'_cpu_before_ns'],t[cpu+'_cpu_after_ns'])
        if t[cpu+'_cpu_after_ns']-t[cpu+'_cpu_before_ns']>wall:
            raise ValueError('CPU within wall bracket')
    if draw['post'] is not None:
        ordered(t['begin_ns'],draw['post']['begin_ns'],draw['post']['end_ns'],t['end_ns'])
        for cpu in ('process','thread'):
            ordered(t[cpu+'_cpu_before_ns'],draw['post'][cpu+'_cpu_ns'],t[cpu+'_cpu_after_ns'])
    return {'id':event['id'],'delay_ns':event['draw_start_ns']-draw['wait']['return_ns'],
            'draw_wait_lateness_ns':draw['wait']['return_ns']-event['onset_ns'],
            'trial_wall_ns':wall,'trial_process_cpu_ns':t['process_cpu_after_ns']-t['process_cpu_before_ns'],
            'trial_thread_cpu_ns':t['thread_cpu_after_ns']-t['thread_cpu_before_ns'],
            'snapshot_wall_ns':0 if draw['post'] is None else draw['post']['end_ns']-draw['post']['begin_ns'],
            'paint_ns':event['draw_end_ns']-event['draw_start_ns'],
            'exposure_ns':event['clear_start_ns']-event['draw_end_ns']}

def validate_cell(spec,data):
    source,capture,life=data['source'],data['capture'],data['lifecycle']
    if any(type(life[k+'_exit']) is not int or life[k+'_exit']!=0 for k in ('fixture','observer')):
        raise ValueError('source/observer terminal0')
    if (type(life['xvfb_exit']) is not int or life['xvfb_exit'] not in (0,-15) or
        life['xvfb_running_before_cleanup'] is not True or life['xvfb_shutdown_requested']!='SIGTERM'):
        raise ValueError('server live until planned SIGTERM shutdown, no forced kill')
    if any(type(life[k+'_pid']) is not int or life[k+'_pid']<=0 for k in ('fixture','observer','xvfb')):
        raise ValueError('positive typed child PID')
    if len({life[k+'_pid'] for k in ('fixture','observer','xvfb')})!=3:
        raise ValueError('distinct child identities')
    if (source['pid']!=life['fixture_pid'] or capture['pid']!=life['observer_pid'] or
            source['window']!=capture['window'] or source['epoch_ns']!=capture['epoch_ns']):
        raise ValueError('native PID/window/epoch join')
    if any(type(obj[key]) is not int or obj[key]<=0 for obj in (source,capture) for key in ('pid','window','epoch_ns')):
        raise ValueError('typed native PID/window/epoch')
    if (data['epoch']!={'epoch_ns':source['epoch_ns']} or
        data['fixture_ready']!={'pid':source['pid'],'window':source['window']} or
        data['observer_ready']!={'pid':capture['pid'],'initial_keymap':'00'*32}):
        raise ValueError('authoritative epoch/readiness join')
    display=data['display_ready']
    if (set(display)!={'pid','display','transport'} or display['pid']!=life['xvfb_pid'] or
        type(display['pid']) is not int or display['transport']!='child-owned-displayfd' or
        not isinstance(display['display'],str) or not display['display'].startswith(':') or
        not display['display'][1:].isdigit()): raise ValueError('private server displayfd identity')
    if capture['initial_keymap']!='00'*32 or capture['final_keymap']!='00'*32 or source['final_keymap']!='00'*32:
        raise ValueError('neutral input final state')
    if source['final_pixels']!=[0]*1024: raise ValueError('source final clear')
    if source['treatment']!=spec['treatment']: raise ValueError('source treatment join')
    events,waits,frames=source['events'],source['wait_traces'],capture['frames']
    n=8 if spec['kind']=='pulse' else 1 if spec['kind']=='persistent' else 0
    if len(events)!=n or len(waits)!=2*n or len(frames)!=8:
        raise ValueError('complete event/wait/frame budget')
    if waits!=data['source_waits'] or frames!=data['frames']:
        raise ValueError('authoritative journal equality')
    if len(data['observer_waits'])!=8:
        raise ValueError('observer journal budget')
    epoch=source['epoch_ns']; metrics=[]; expected_journal=[]
    for i,e in enumerate(events):
        identity=i+1
        due=epoch+(120*i+12)*1_000_000 if spec['kind']=='pulse' else epoch-20_000_000
        clear=due+10_000_000 if spec['kind']=='pulse' else epoch+1_000_000_000
        if (e['id']!=identity or e['color']!=(0xFF0000 if identity%2 else 0x00FF00) or
                e['onset_ns']!=due or e['due_clear_ns']!=clear):
            raise ValueError('frozen source pulse/control plan')
        metrics.append(validate_event(e,waits[2*i],waits[2*i+1],spec['treatment']))
        if i: ordered(events[i-1]['clear_end_ns'],waits[2*i]['pre']['begin_ns'])
        expected_journal.extend([{'event':k,'id':identity,'start':e[k+'_start_ns'],'end':e[k+'_end_ns']}
                                 for k in ('draw','clear')])
    if expected_journal!=data['source_journal']: raise ValueError('paint journal equality')
    decoded=[]; capture_lateness=[]; starts=[]
    previous=capture['epoch_read_ns']
    for i,f in enumerate(frames):
        due=epoch+(120*i+10*[0,3,6,9][i%4]+5)*1_000_000
        receipt={k:f[k] for k in ('index','due_ns','pre','wait','post')}
        if (type(f['index']) is not int or f['index']!=i or f['due_ns']!=due or
                receipt!=data['observer_waits'][i] or f['post'] is None):
            raise ValueError('exact observer stream/schedule join')
        # Observer shares pacing but has acquisition rather than paint endpoints.
        ordered(previous,f['pre']['begin_ns'])
        wait_valid({**f,'paint_start_ns':f['start_ns'],'paint_end_ns':f['extracted_ns']},due)
        ordered(f['start_ns'],f['native_return_ns'],f['extracted_ns'])
        previous=f['extracted_ns']
        raw=base64.b64decode(f['pixels_b64'],validate=True)
        if len(raw)!=4096 or hashlib.sha256(raw).hexdigest()!=f['pixel_sha256']:
            raise ValueError('exact pixel byte custody')
        pixels=list(struct.unpack('<1024I',raw))
        color=pixels[1]; identity=pixels[0]
        hit=({'id':identity,'color':color} if identity in range(1,9) and
              color in (0xFF0000,0x00FF00) and pixels[1:]==[color]*1023 else None)
        if hit!=f['decoded']: raise ValueError('independent visual decode')
        if hit:
            matching=[e for e in events if e['id']==hit['id'] and e['color']==hit['color']]
            if len(matching)!=1: raise ValueError('no false visual attribution')
            if not (f['native_return_ns']>=matching[0]['draw_start_ns'] and f['start_ns']<=matching[0]['clear_end_ns']):
                raise ValueError('decoded cue impossible in acquisition interval')
        elif pixels!=[0]*1024: raise ValueError('unknown native pixel pattern')
        decoded.append(hit); starts.append(f['start_ns']); capture_lateness.append(f['start_ns']-due)
    if spec['kind']=='dark' and any(decoded): raise ValueError('dark false detection')
    if spec['kind']=='persistent' and decoded!=[{'id':1,'color':0xFF0000}]*8:
        raise ValueError('persistent cue control')
    if spec['kind']=='persistent' and any(not (events[0]['draw_end_ns']<=f['start_ns'] and
         f['extracted_ns']<=events[0]['clear_start_ns']) for f in frames):
        raise ValueError('persistent stable acquisition')
    source_snapshots=[s for w in waits for s in (w['pre'],w['post']) if s is not None]
    observer_snapshots=[s for f in frames for s in (f['pre'],f['post'])]
    for snapshots in (source_snapshots,observer_snapshots):
        for before,after in zip(snapshots,snapshots[1:]):
            ordered(before['end_ns'],after['begin_ns'])
            for name in ('process_cpu_ns','thread_cpu_ns','voluntary','involuntary'):
                ordered(before[name],after[name])
            for name in ('schedstat','cpu_stat_local'):
                b,a=before[name],after[name]
                if b['available'] and a['available']:
                    if name=='schedstat':
                        bv,av=[int(x) for x in b['raw'].split()],[int(x) for x in a['raw'].split()]
                    else:
                        bd={k:int(v) for k,v in (x.split() for x in b['raw'].splitlines())}
                        ad={k:int(v) for k,v in (x.split() for x in a['raw'].splitlines())}
                        if set(bd)!=set(ad): raise ValueError('local counter key continuity')
                        bv,av=list(bd.values()),[ad[k] for k in bd]
                    if any(y<x for x,y in zip(bv,av)): raise ValueError('optional counter regression')
    snapshots=sorted(source_snapshots+observer_snapshots,key=lambda s:s['cpu_read_end_ns'])
    for i,after in enumerate(snapshots):
        candidates=[s for s in snapshots[:i] if s['cpu_read_end_ns']<=after['cpu_read_begin_ns']]
        if candidates:
            before=candidates[-1]
            for name in ('usage_usec','nr_periods','nr_throttled','throttled_usec'):
                ordered(before['cpu_stat'][name],after['cpu_stat'][name])
    # Timing quality is an outcome; never truncate/censor the matched diagnostic.
    gaps=[b-a for a,b in zip([epoch]+starts,starts+[epoch+960_000_000])]
    return {'id':spec['id'],'kind':spec['kind'],'pair':spec['pair'],'treatment':spec['treatment'],
            'events':metrics,'delays_ns':[x['delay_ns'] for x in metrics],
            'max_capture_lateness_ns':max(capture_lateness),'max_capture_gap_ns':max(gaps),
            'scientific_exposure_eligible':all(5_000_000<=x['exposure_ns']<=15_000_000 for x in metrics)
              if spec['kind']=='pulse' else None}
