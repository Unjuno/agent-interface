"""Independent raw-only reconstruction. Imports neither Pillow nor tested policies.

This is a separately implemented, same-author audit, not external peer review.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,statistics,sys
from functools import lru_cache
from pathlib import Path
from png_oracle import decode

ROOT=Path(__file__).resolve().parent
CAP=262144; CHUNK=65536

def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text())
def same(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
def need(x,msg):
    if not x:raise ValueError(msg)
def integer(x,msg):need(type(x)is int,msg);return x

@lru_cache(maxsize=256)
def blob(h):
    need(type(h)is str and len(h)==64,'bad content key')
    raw=(ROOT/'blobs'/h).read_bytes();need(sha(raw)==h,'blob digest');return raw

@lru_cache(maxsize=64)
def pixels(h):return decode(blob(h))

def check_files(files):
    need(type(files)is dict,'files map')
    for name,meta in files.items():
        need(type(name)is str and '/' not in name and name.endswith('.png'),'file name')
        need(integer(meta['bytes'],'byte count')==len(blob(meta['sha256'])),'file size')

def input_data(fixture):
    b=(ROOT/fixture['path']).read_bytes();need(sha(b)==fixture['sha256'],'input digest');return b

def expected_inspection(raw,pin,mode):
    if raw is None:return 'UNAVAILABLE'
    if len(raw)!=len(blob(pin)):return 'LENGTH_MISMATCH'
    return 'MATCH' if sha(raw)==pin else 'DIGEST_MISMATCH'

def check_probe(probe,pin,mode,final_files):
    need(type(probe)is dict,'missing probe')
    need(same(probe['before_files'],final_files) and same(probe['after_files'],final_files),'probe mutated files')
    n=len(blob(pin))
    for key in ('accounting','memory_result'):
        p=probe[key];need(p['status']=='MATCH' and p['digest']==pin,'probe digest')
        for field in ('read_bytes','hash_bytes','read_calls','max_request_bytes'):integer(p[field],'probe '+field)
        need(p['read_bytes']==n and p['hash_bytes']==n,'probe complete hash')
        if mode=='FULL_PIN':expected=[[n+1,n]]
        else:
            expected=[[CHUNK,CHUNK] for _ in range(n//CHUNK)]
            if n%CHUNK:expected.append([n%CHUNK,n%CHUNK])
            expected.append([1,0])
        need(p['read_calls']==len(expected),'probe calls')
        need(p['max_request_bytes']==max(x[0] for x in expected),'probe buffer bound')
        need(same(p['segments'],expected if key=='accounting' else []),'probe segments')
    need(integer(probe['traced_current_bytes'],'current memory')>=0,'negative current memory')
    need(integer(probe['traced_peak_bytes'],'peak memory')>=probe['traced_current_bytes'],'invalid memory peak')


def check_case(rec,case,fixture,worker_cpu):
    need(same(rec['case'],case),'case identity')
    need(integer(rec['pid'],'pid')>0,'invalid pid')
    need(same(rec['affinity'],[worker_cpu]),'affinity')
    need(integer(rec['started_ns'],'case start') < integer(rec['ended_ns'],'case end'),'case clocks')
    pubs=rec['publications'];expected_count=9 if case['kind']=='performance' else (2 if case['scenario']=='NEXT_NAME_OCCUPIED' else 3)
    need(len(pubs)==expected_count,'publication denominator')
    original=input_data(fixture);current=original;previous=None;pin=None;prior_files={};last_end=rec['started_ns']
    warm_ns=[];warm_cpu=[];new_count=0;reuse_count=0
    for index,row in enumerate(pubs):
        check_files(row['files'])
        need(integer(row['start_ns'],'start')>=last_end,'publication order')
        need(integer(row['end_ns'],'end')>=row['start_ns'],'time direction')
        need(integer(row['cpu_end_ns'],'cpu end')>=integer(row['cpu_start_ns'],'cpu start'),'cpu direction')
        last_end=row['end_ns']
        expected_label='initial' if index==0 else ('warm-'+str(index-1) if case['kind']=='performance' else ('post-maintenance' if index==1 else 'steady-after'))
        need(row['label']==expected_label,'publication label')
        if case['kind']=='control' and index==1:
            m=rec['maintenance'];need(m is not None and m['scenario']==case['scenario'],'maintenance identity')
            check_files(m['after_files']);before=blob(pin)
            need(m['before_sha256']==pin,'maintenance base')
            need(pubs[0]['end_ns'] <= integer(m['completed_ns'],'maintenance time') <= row['start_ns'],'maintenance order')
            expected=dict(prior_files);s=case['scenario'];old_name=previous
            if s=='MISSING':expected.pop(old_name)
            elif s in ('TRUNCATED','TAIL_CHANGED','LOSSLESS_REENCODE','APPENDED'):
                actual=blob(m['after_files'][old_name]['sha256'])
                if s=='TRUNCATED':need(actual==before[:len(before)//2],'truncate bytes')
                elif s=='TAIL_CHANGED':
                    target=bytearray(before);target[-32]^=1
                    need(actual==bytes(target) and len(before)-32>CAP,'tail changed bytes')
                elif s=='APPENDED':need(actual==before+b'bounded-appended-data\n','append bytes')
                else:
                    need(actual!=before,'reencoded identity unchanged')
                    w,h,rgb=decode(actual);need((w,h)==(fixture['width'],fixture['height']) and rgb==original,'reencode pixel equality')
                expected[old_name]=m['after_files'][old_name]
            elif s in ('FRAME_CHANGED','NEXT_NAME_OCCUPIED'):
                altered=bytearray(original);altered[0]^=1;current=bytes(altered)
                if s=='NEXT_NAME_OCCUPIED':
                    target=m['after_files']['002.png'];need(blob(target['sha256'])==b'owned collision sentinel\n','sentinel changed')
                    expected['002.png']=target
            else:raise ValueError('unknown maintenance')
            need(same(expected,m['after_files']),'unplanned maintenance')
            prior_files=m['after_files']
        need(row['input_sha256']==sha(current),'requested input')
        same_frame=index>0 and pubs[index-1]['input_sha256']==row['input_sha256']
        cache_raw=blob(prior_files[previous]['sha256']) if previous in prior_files else None
        if not same_frame:guard='NOT_NEEDED';valid=False
        elif case['policy']=='LEGACY_256K':
            if cache_raw is None or len(cache_raw)>CAP:guard='INVALID_OR_MISSING';valid=False
            else:valid=sha(cache_raw)==pin;guard='MATCH' if valid else 'MISMATCH'
        else:
            guard=expected_inspection(cache_raw,pin,case['policy']);valid=guard=='MATCH'
        will_reuse=same_frame and valid
        new_name=f'{index+1:03d}.png'
        collision=not will_reuse and new_name in prior_files
        if collision:
            need(row['error']=='FileExistsError' and row['response'] is None,'collision refusal')
            need(same(row['files'],prior_files),'collision overwrite')
            continue
        need(row['error'] is None and row['response'] is not None,'unexpected refusal')
        response=row['response'];receipt=response['receipt']
        need(response['authority']=='none' and response['input_dispatched'] is False,'authority')
        need(type(response['model_calls'])is int and response['model_calls']==0,'model calls')
        actual_guard=response['guard'] if case['policy']=='LEGACY_256K' else response['guard']['status']
        need(actual_guard==guard,'guard decision')
        need(type(receipt['image_reused'])is bool and receipt['image_reused']==will_reuse,'reuse decision')
        need(row['output_name']==(previous if will_reuse else new_name),'output path selection')
        need(Path(receipt['image']).name==row['output_name'],'receipt path')
        need(row['output_sha256']==row['files'][row['output_name']]['sha256'],'output file binding')
        w,h,rgb=pixels(row['output_sha256'])
        need((w,h)==(fixture['width'],fixture['height']) and rgb==current,'wrong output pixels')
        expected=dict(prior_files)
        if not will_reuse:
            new_count+=1;pin=row['output_sha256'];previous=new_name;expected[new_name]=row['files'][new_name]
        else:reuse_count+=1
        need(same(expected,row['files']),'unplanned file mutation')
        if case['policy']!='LEGACY_256K':
            registration=response['registration']
            if will_reuse:need(registration is None,'unexpected registration')
            else:
                need(registration['status']=='MATCH' and registration['digest']==pin,'registration')
                need(type(registration['hash_bytes'])is int and registration['hash_bytes']==len(blob(pin)),'registration complete hash')
            if guard in ('MATCH','DIGEST_MISMATCH'):
                g=response['guard'];need(g['digest']==sha(cache_raw),'guard digest')
                need(type(g['hash_bytes'])is int and g['hash_bytes']==len(cache_raw),'guard full hash')
                if case['policy']=='STREAM_PIN':need(g['max_request_bytes']<=CHUNK,'guard chunk bound')
        if index and case['kind']=='performance':
            warm_ns.append(row['end_ns']-row['start_ns']);warm_cpu.append(row['cpu_end_ns']-row['cpu_start_ns'])
        prior_files=row['files']
    need(same(rec['final_files'],pubs[-1]['files']),'final files')
    need(rec['ended_ns']>=last_end,'case end before output')
    if case['kind']=='performance':
        need(rec['maintenance'] is None,'performance maintenance')
        if case['policy']!='LEGACY_256K':check_probe(rec['probe'],pin,case['policy'],rec['final_files'])
        else:need(rec['probe'] is None,'legacy undocumented probe')
    else:need(rec['probe'] is None,'control undocumented probe')
    return {'id':case['id'],'image':case['image'],'policy':case['policy'],'kind':case['kind'],
            'rep':case['rep'],'scenario':case['scenario'],'publications':len(pubs),
            'new_files':new_count,'reused':reuse_count,'warm_wall_ns':sum(warm_ns),'warm_cpu_ns':sum(warm_cpu),
            'png_bytes':len(blob(pubs[0]['output_sha256'])),
            'memory_peak_bytes':None if rec['probe'] is None else rec['probe']['traced_peak_bytes']}


def mutations(records,schedule,fixtures,cpu):
    checks={}
    p=next(i for i,c in enumerate(schedule) if c['kind']=='performance' and c['policy']=='STREAM_PIN' and c['image']=='noise640')
    c=next(i for i,x in enumerate(schedule) if x['scenario']=='TAIL_CHANGED' and x['policy']=='STREAM_PIN')
    tests=[('case_identity',p,lambda r:r['case'].update(rep=True)),
           ('affinity',p,lambda r:r.update(affinity=[99])),
           ('publication_missing',p,lambda r:r['publications'].pop()),
           ('clock_reversed',p,lambda r:r['publications'][1].update(end_ns=0)),
           ('output_digest',p,lambda r:r['publications'][1].update(output_sha256='0'*64)),
           ('reuse_flag',p,lambda r:r['publications'][1]['response']['receipt'].update(image_reused=False)),
           ('hash_prefix_only',p,lambda r:r['probe']['accounting'].update(hash_bytes=65536)),
           ('oversized_read',p,lambda r:r['probe']['accounting'].update(max_request_bytes=900000)),
           ('digest_changed',p,lambda r:r['probe']['memory_result'].update(digest='0'*64)),
           ('boolean_peak',p,lambda r:r['probe'].update(traced_peak_bytes=True)),
           ('tail_falsely_matched',c,lambda r:r['publications'][1]['response']['guard'].update(status='MATCH')),
           ('input_authority',p,lambda r:r['publications'][1]['response'].update(input_dispatched=True))]
    for name,i,change in tests:
        r=copy.deepcopy(records[i]);change(r)
        try:check_case(r,schedule[i],fixtures[schedule[i]['image']],cpu)
        except (ValueError,KeyError,TypeError,FileNotFoundError):checks[name]=True
        else:checks[name]=False
    return checks


def audit(controls=False):
    freeze=load(ROOT/'FREEZE.json');freeze_sha=sha((ROOT/'FREEZE.json').read_bytes())
    for name,digest in freeze['sha256'].items():need(sha((ROOT/name).read_bytes())==digest,'source: '+name)
    schedule=load(ROOT/'SCHEDULE.json');need(len(schedule)==87 and len({c['id'] for c in schedule})==87,'schedule denominator')
    fixtures={x['id']:x for x in load(ROOT/'FIXTURES.json')};cpu=load(ROOT/'ENVIRONMENT.json')['worker_cpu']
    records=[];rows=[];elapsed=[]
    for batch in range(7):
        path=ROOT/'formal'/f'batch-{batch:02d}';planned=[c for c in schedule if c['batch']==batch]
        end=load(path/'END.json');outer=load(path/'EXTERNAL_EXIT.json');start=load(path/'START.json')
        need(type(outer['returncode'])is int and outer['returncode']==0 and outer['timeout'] is False,'outer exit')
        need(type(outer['batch'])is int and outer['batch']==batch,'outer identity')
        need(sha((path/'outer.stdout').read_bytes())==outer['stdout_sha256'] and sha((path/'outer.stderr').read_bytes())==outer['stderr_sha256'],'outer bytes')
        need((path/'outer.stderr').read_bytes()==b'','outer stderr')
        need(same(end['cases'],[c['id'] for c in planned]) and same(start['cases'],end['cases']),'batch coverage')
        need(start['freeze_sha256']==end['freeze_sha256']==freeze_sha,'batch source binding')
        need(outer['started_ns']<=start['started_ns']<end['ended_ns']<=outer['ended_ns'],'outer interval')
        need(outer['ended_ns']-outer['started_ns']<=33_000_000_000,'outer budget')
        elapsed.append(outer['ended_ns']-outer['started_ns'])
        for case in planned:
            rec_path=path/case['id']/'RESULT.json';receipt=load(path/(case['id']+'.exit.json'))
            need(type(receipt['returncode'])is int and receipt['returncode']==0 and receipt['timeout'] is False,'worker exit')
            need(receipt['id']==case['id'] and receipt['stderr']=='','worker receipt')
            need(type(receipt['end_ns'])is int and receipt['end_ns']-receipt['start_ns']<=8_500_000_000,'worker budget')
            digest=sha(rec_path.read_bytes());wire=json.loads(receipt['stdout'])
            need(end['result_hashes'][case['id']]==wire['result_sha256']==digest,'result byte binding')
            rec=load(rec_path);need(rec['freeze_sha256']==freeze_sha and rec['pid']==wire['pid'],'worker source/process identity')
            need(receipt['start_ns']<=rec['started_ns']<=rec['ended_ns']<=receipt['end_ns'],'worker enclosure')
            records.append(rec);rows.append(check_case(rec,case,fixtures[case['image']],cpu))
    # Gathering follows schedule order; no case is pooled from construction.
    need([r['id'] for r in rows]==[c['id'] for c in schedule],'case order')
    perf=[r for r in rows if r['kind']=='performance'];groups={}
    for image in fixtures:
        groups[image]={}
        for policy in ('LEGACY_256K','FULL_PIN','STREAM_PIN'):
            cell=[r for r in perf if r['image']==image and r['policy']==policy]
            need(len(cell)==5,'repetition denominator')
            groups[image][policy]={'png_bytes':cell[0]['png_bytes'],
                'warm_wall_ns':{'min':min(r['warm_wall_ns'] for r in cell),'median':statistics.median(r['warm_wall_ns'] for r in cell),'max':max(r['warm_wall_ns'] for r in cell)},
                'warm_cpu_ns':{'min':min(r['warm_cpu_ns'] for r in cell),'median':statistics.median(r['warm_cpu_ns'] for r in cell),'max':max(r['warm_cpu_ns'] for r in cell)},
                'files_each':[r['new_files'] for r in cell],
                'peak_bytes_each':[r['memory_peak_bytes'] for r in cell]}
    need(groups['noise256']['STREAM_PIN']['png_bytes']<=CAP,'small input stratum')
    for image in ('noise320','noise640'):
        need(CAP<groups[image]['STREAM_PIN']['png_bytes']<=4*1024*1024,'large input stratum')
    for row in perf:
        required=9 if row['policy']=='LEGACY_256K' and row['png_bytes']>CAP else 1
        need(row['new_files']==required and row['reused']==9-required,'warm file/reuse accounting')
    ratios={}
    for image in ('noise320','noise640'):
        vals=[]
        for rep in range(5):
            a=next(r for r in perf if r['image']==image and r['rep']==rep and r['policy']=='LEGACY_256K')
            b=next(r for r in perf if r['image']==image and r['rep']==rep and r['policy']=='STREAM_PIN')
            vals.append(b['warm_wall_ns']/a['warm_wall_ns'])
        ratios[image]=vals
    memory_ratios=[]
    for rep in range(5):
        full=next(r for r in perf if r['image']=='noise640' and r['rep']==rep and r['policy']=='FULL_PIN')
        stream=next(r for r in perf if r['image']=='noise640' and r['rep']==rep and r['policy']=='STREAM_PIN')
        memory_ratios.append(stream['memory_peak_bytes']/full['memory_peak_bytes'])
    memory_gate=(max(groups['noise640']['STREAM_PIN']['peak_bytes_each'])<=3*CHUNK and statistics.median(memory_ratios)<=0.25)
    timing_gate=all(statistics.median(v)<=0.5 for v in ratios.values())
    mutation_results=mutations(records,schedule,fixtures,cpu) if controls else None
    if controls:need(all(mutation_results.values()),'corruption control accepted')
    return {'decision':'PASS_STREAMING_REUSE_CONTRACT_SCOPED','scientific_contract_pass':True,
            'timing_decision':'PASS_LOCAL_REUSE_TIME_SCOPED' if timing_gate else 'HOLD_LOCAL_TIME',
            'memory_decision':'PASS_TRACED_ALLOCATION_BOUND_SCOPED' if memory_gate else 'HOLD_MEMORY',
            'formal_cases':len(rows),'publications':sum(r['publications'] for r in rows),
            'batch_elapsed_ns':elapsed,'errors':[], 'groups':groups,'paired_stream_legacy_time_ratios':ratios,
            'paired_stream_full_peak_ratios':memory_ratios,'controls':mutation_results,'rows':rows,
            'limits':['Python traced allocations are not RSS or decoder/native total memory',
                      'generated RGB fixture; no GUI/model/task benefit',
                      'local preregistration only; no GitHub write path in this session',
                      'same-author independent implementation is not external review']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--controls',action='store_true');args=parser.parse_args()
    try:result=audit(args.controls)
    except Exception as exc:
        result={'decision':'HOLD_EVIDENCE_INTEGRITY','errors':[type(exc).__name__+': '+str(exc)]}
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False));sys.exit(bool(result['errors']))
