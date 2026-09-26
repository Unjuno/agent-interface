"""Independent raw-byte/trace auditor. No worker or snapshot imports."""
import argparse,copy,hashlib,json,statistics,sys
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()+b'\n'
def need(v,msg):
    if not v:raise ValueError(msg)
def ii(v):return type(v) is int

def check(raw,data,n,rep):
    need(raw['schema']=='snapshot-index-density-c5d2-v1','schema')
    need(ii(raw['n']) and raw['n']==n and ii(raw['rep']) and raw['rep']==rep,'row identity')
    total=raw['total_bytes'];need(ii(total) and total>0 and len(data)==total and total%n==0,'constant bytes')
    need(raw['input_sha256']==sha(data),'source hash');need(raw['input_is_reused_object'] is True and raw['input_unchanged'] is True,'input immutability')
    need(raw['affinity']==[0] and all(ii(a) for a in raw['affinity']) and ii(raw['pid']) and raw['pid']>0,'process identity')
    width=total//n;lines=data.splitlines(keepends=True);need(len(lines)==n,'line count')
    items=[]
    for i,line in enumerate(lines,1):
        item={'event':'notification','delivery_id':'delivery:'+str(i),'value':'item-%06d'%i};b=enc(item)
        need(line==b[:-1]+b' '*(width-len(b))+b'\n','fixture bytes');items.append(item)
    entries=raw['prefix_entries'];need(len(entries)==n+1,'entry count')
    h=hashlib.sha256();expected=[{'offset':0,'sequence':1,'sha256':h.hexdigest()}]
    for i,line in enumerate(lines,1):
        h.update(line);expected.append({'offset':i*width,'sequence':i+1,'sha256':h.hexdigest()})
    need(entries==expected,'prefix inventory')
    response=raw['response'];p=min(32,n)
    wanted={'schema':'agent-interface/experimental-inbox-read-v1','records':items[:p],'tail_state':'limit' if p<n else 'end','problem':None,
            'next_cursor':{'schema':'agent-interface/experimental-read-cursor-v1','stream_id':'density-c5d2','offset':p*width,'next_sequence':p+1,'prefix_sha256':sha(data[:p*width])},
            'authority':'none','acknowledged':False,'input_dispatched':False}
    need(response==wanted,'response');need(response['acknowledged'] is False and response['input_dispatched'] is False,'neutral booleans')
    need(raw['metadata']=={'source_role':'historical_byte_snapshot','snapshot_sha256':sha(data),'snapshot_bytes':len(data),'stream_id':'density-c5d2','current_file_verified':False,'producer_lifetime_verified':False,'authority':'none','acknowledged':False,'input_dispatched':False},'metadata')
    need(raw['traceback_limit']==1 and ii(raw['traceback_limit']),'traceback depth');need(len(raw['traces'])>0,'trace existence')
    by_source=0
    for t in raw['traces']:
        need(set(t)=={'size','domain','filename','line'},'trace fields')
        need(ii(t['size']) and t['size']>0 and ii(t['domain']) and t['domain']>=0 and ii(t['line']) and t['line']>0 and isinstance(t['filename'],str),'trace types')
        if t['filename']=='eager_snapshot.py':by_source+=t['size']
    total_trace=sum(t['size'] for t in raw['traces'])
    need(ii(raw['trace_bytes']) and raw['trace_bytes']==total_trace,'trace sum')
    need(ii(raw['eager_source_trace_bytes']) and raw['eager_source_trace_bytes']==by_source and by_source>0,'attribution sum')
    return {'n':n,'rep':rep,'trace_bytes':total_trace,'eager_source_trace_bytes':by_source,'trace_blocks':len(raw['traces']),'prefix_entries':len(entries)}

def run(root):
    f=json.loads((root/'FREEZE.json').read_bytes())
    for n,h in f['sources'].items():need(sha((root/n).read_bytes())==h,'SOURCE_MISMATCH:'+n)
    d=root/'formal-01';e=json.loads((d/'EXECUTION.json').read_bytes())
    need(ii(e['returncode']) and e['returncode']==0,'orchestrator exit')
    need(e['stdout_sha256']==sha((d/'runner.stdout').read_bytes()) and e['stderr_sha256']==sha((d/'runner.stderr').read_bytes()),'orchestrator bytes')
    need((d/'runner.stdout').read_bytes()==b'COMPLETE_9_CASES\n' and (d/'runner.stderr').read_bytes()==b'','orchestrator output')
    rr=json.loads((d/'RUN.json').read_bytes());need(rr['freeze_sha256']==sha((root/'FREEZE.json').read_bytes()),'freeze identity')
    expected=[]
    for rep in range(3):
        ns=[128,1024,8192];ns=ns[rep:]+ns[:rep]
        expected.extend((n,rep) for n in ns)
    need(len(rr['rows'])==9,'denominator');rows=[];examples=[]
    for rec,(n,rep) in zip(rr['rows'],expected):
        cid=f'n{n}-r{rep}';need(rec['id']==cid and rec['n']==n and rec['rep']==rep,'schedule')
        p=d/cid;need(json.loads((p/'PROCESS.json').read_bytes())==rec,'worker receipt')
        need(ii(rec['returncode']) and rec['returncode']==0,'worker exit')
        data=(p/'input.jsonl').read_bytes();rawbytes=(p/'stdout.json').read_bytes();raw=json.loads(rawbytes)
        need(len(data)==1048576,'formal size')
        need(sha(rawbytes)==rec['stdout_sha256'] and sha((p/'stderr.txt').read_bytes())==rec['stderr_sha256'] and (p/'stderr.txt').read_bytes()==b'','worker bytes')
        need(rec['command'][-4:-1]==[str(n),'1048576',str(rep)] and Path(rec['command'][-1]).name==cid,'worker command')
        need(ii(rec['start_ns']) and ii(rec['end_ns']) and rec['start_ns']<rec['end_ns'],'process chronology')
        rows.append(check(raw,data,n,rep));examples.append((raw,data,n,rep))
    table=[]
    for n in [128,1024,8192]:
        cell=[x for x in rows if x['n']==n];row={'n':n,'line_bytes':1048576//n,'prefix_entries':n+1}
        for field in ['trace_bytes','eager_source_trace_bytes','trace_blocks']:
            a=[x[field] for x in cell];row[field]={'median':statistics.median(a),'min':min(a),'max':max(a)}
        table.append(row)
    ratio=table[-1]['trace_bytes']['median']/table[0]['trace_bytes']['median']
    return {'allocation':'index-density-c5d2-20260922-01','decision':'PASS_INDEX_DENSITY_MEMORY_SCOPED' if ratio>=8 else 'HOLD_DENSITY_MEMORY_MAGNITUDE',
            'rows':rows,'table':table,'high_over_low_trace_ratio':ratio,'errors':[],'formal_cases':9,'all_worker_exits_zero':True,'orchestrator_exit_zero':True},examples

def mutations(examples):
    original,data,n,rep=examples[0];out=[]
    def test(name,fn):
        o=copy.deepcopy(original);fn(o)
        try:check(o,data,n,rep)
        except (ValueError,KeyError,TypeError,IndexError):out.append({'name':name,'rejected':True});return
        raise ValueError('CORRUPTION_ACCEPTED:'+name)
    test('missing_prefix',lambda x:x['prefix_entries'].pop())
    test('changed_prefix',lambda x:x['prefix_entries'][2].update(sha256='0'*64))
    test('changed_trace_size',lambda x:x['traces'][0].update(size=x['traces'][0]['size']+1))
    test('missing_trace',lambda x:x['traces'].pop())
    test('boolean_trace',lambda x:x['traces'][0].update(size=True))
    test('false_sum',lambda x:x.update(trace_bytes=x['trace_bytes']+1))
    test('source_identity',lambda x:x.update(input_sha256='0'*64))
    test('wrong_payload',lambda x:x['response']['records'][0].update(value='wrong'))
    test('authority',lambda x:x['response'].update(authority='input'))
    test('wrong_role',lambda x:x['metadata'].update(current_file_verified=True))
    return out
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('root',type=Path);o=a.parse_args()
    try:
        result,ex=run(o.root);result['corruption_controls']=mutations(ex);sys.stdout.buffer.write(enc(result))
    except (OSError,ValueError,KeyError,TypeError,IndexError) as e:
        sys.stdout.buffer.write(enc({'decision':'HOLD_AUDIT_INCOMPLETE','error':str(e)}));sys.exit(2)
