import hashlib
import json
import os
import pathlib
import sys

ORIGINAL='a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e'
CANDIDATE='dca770e5e0c532b301b12032c9532bd5fae602947caff4fff21bde60634a57f1'
CASES=('healthy','json_fault','ready_then_fault','array','utf8_fault','eof_live')
PAYLOADS={'healthy':[b'{"event":"ready","fixture":"E02"}\n'],
          'json_fault':[b'{"event":\n'],
          'ready_then_fault':[b'{"event":"ready","fixture":"E02"}\n',b'{"event":\n'],
          'array':[b'[1]\n'],'utf8_fault':[b'\xff\n'],'eof_live':[b'']}

def closed(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise ValueError('duplicate JSON key')
        out[key]=value
    return out

def check(root):
    names={'SUMMARY.json','RUNTIME.json'}|{c+s for c in CASES for s in ('-result.json','-peer.jsonl')}
    if {p.name for p in root.iterdir()}!=names: raise ValueError('closed receipt set')
    raw={}
    for name in names:
        p=root/name
        if p.is_symlink() or not p.is_file(): raise ValueError('nonregular receipt')
        raw[name]=p.read_bytes()
    read=lambda n:json.loads(raw[n],object_pairs_hook=closed)
    summary=read('SUMMARY.json');runtime=read('RUNTIME.json')
    if type(summary['native_runs']) is not int or summary['native_runs']!=1 or type(summary['retries']) is not int or summary['retries']!=0 or type(summary['timeout_override_seconds']) not in (int,float) or summary['timeout_override_seconds']!=.35: raise ValueError('allocation counts/override')
    if type(runtime['python']) is not str or not runtime['python'].startswith('3.12.') or type(runtime['cgroup']) is not str or '0::' not in runtime['cgroup']: raise ValueError('runtime evidence')
    if summary['status']!='COMPLETE' or summary['runtime']!=runtime: raise ValueError('completion runtime')
    if runtime['original_sha256']!=ORIGINAL or runtime['candidate_sha256']!=CANDIDATE: raise ValueError('source identity')
    if type(runtime['pid']) is not int or runtime['pid']<=0 or type(runtime['uid']) is not int or runtime['uid']!=501 or runtime['limits']!={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}: raise ValueError('runtime allocation')
    rows=[]
    expected=[['ready'],['_SessionReaderFailure'],['ready','_SessionReaderFailure'],['TypeError'],['_SessionReaderFailure'],['TimeoutError']]
    finding=True
    for i,case in enumerate(CASES):
        row=read(case+'-result.json')
        peers=[json.loads(line,object_pairs_hook=closed) for line in raw[case+'-peer.jsonl'].splitlines()]
        if len(peers)!=len(PAYLOADS[case]): raise ValueError('emitter cardinality')
        if type(row['pid']) is not int or type(row['producer_pid']) is not int or row['producer_pid']!=runtime['pid'] or row['case']!=case: raise ValueError('PID identity')
        for peer,payload in zip(peers,PAYLOADS[case]):
            if type(peer['pid']) is not int or type(peer['ppid']) is not int or peer['pid']!=row['pid'] or peer['ppid']!=runtime['pid'] or peer['hex']!=payload.hex() or type(peer['written']) is not int or peer['written']!=len(payload): raise ValueError('emitter payload identity')
            if peer['kind']!=('stdout-close' if case=='eof_live' else 'write'): raise ValueError('emitter boundary')
            if any(type(peer[k]) is not int or peer[k]<=0 for k in ('start_ns','return_ns','monotonic_ns')) or not peer['start_ns']<=peer['return_ns']<=peer['monotonic_ns']: raise ValueError('emitter chronology')
        if row['child_alive'] is not True or type(row['reader_alive']) is not bool or type(row['cleanup_exit']) is not int or row['cleanup_exit']!=0 or row['reader_retired'] is not True or row['fatal'] is not None or row['cleanup_faults'] or row['unhandled']: raise ValueError('custody cleanup')
        outcomes=[r['outcome'] for r in row['results']]
        for result in row['results']:
            if any(type(result[k]) is not int or result[k]<=0 for k in ('start_ns','end_ns','elapsed_ns')) or result['end_ns']-result['start_ns']!=result['elapsed_ns']: raise ValueError('wait chronology')
        if peers[0]['start_ns']>row['results'][0]['end_ns']: raise ValueError('emission after result')
        if case=='ready_then_fault' and len(row['results'])==2:
            h=row['handshake']
            if any(type(h[k]) is not int for k in ('ready_return_ns','continue_start_ns','continue_return_ns')) or h['ready_return_ns']!=row['results'][0]['end_ns'] or not h['ready_return_ns']<=h['continue_start_ns']<=h['continue_return_ns']<=row['results'][1]['start_ns'] or not h['continue_start_ns']<=peers[1]['start_ns']<=row['results'][1]['end_ns']: raise ValueError('handshake chronology')
        elif row['handshake'] is not None: raise ValueError('unexpected handshake')
        finding &= outcomes==expected[i] and row['reader_alive']==(case in ('healthy','array'))
        parsed=[{'event':'ready','fixture':'E02'}] if case in ('healthy','ready_then_fault') else ([[1]] if case=='array' else [])
        finding &= row['parsed_events']==parsed
        if outcomes==expected[i] and case in ('json_fault','ready_then_fault','utf8_fault'):
            cause=row['results'][-1]['cause']
            if not isinstance(cause,dict): finding=False
            else:
                finding &= cause['type']==('UnicodeDecodeError' if case=='utf8_fault' else 'JSONDecodeError')
                if case=='utf8_fault': finding &= cause['object_hex']=='ff0a'
                else: finding &= cause['doc']=='{"event":\n'
        rows.append(row)
    if rows!=summary['rows']: raise ValueError('summary row disagreement')
    return ('PASS_CANDIDATE_READER_SIGNAL' if finding else 'HOLD_EXPECTATION_NOT_MET'),{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}

if __name__=='__main__':
    output=pathlib.Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=False)
    try:
        verdict,hashes=check(pathlib.Path(sys.argv[1]));result=dict(status='PASS_SAVED_DIAGNOSTIC_AUDIT',verdict=verdict,hashes=hashes,uid=os.getuid());code=0
    except Exception as exc: result=dict(status='FAIL_SAVED_DIAGNOSTIC_AUDIT',error=repr(exc),uid=os.getuid());code=1
    (output/'AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result));sys.exit(code)
