"""Bounded serial subprocess experiment. New output only; no formal reruns."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from urllib.parse import quote
from policy import classify

ROOT = Path(__file__).resolve().parent
SCENARIOS = ['RETAINED_APPLIED','RETIRED_APPLIED','RETIRED_NEVER_ACCEPTED',
             'RETIRED_CHANGED_PAYLOAD','FRESH_NEW_INTENT','RETAINED_CHANGED_PAYLOAD',
             'WRONG_SESSION','BOOLEAN_EPOCH']
POLICIES = ['LOOKUP_ONLY','COVERAGE_AWARE']
BASE = {'session':'fixture-session','resource':'counter','epoch':7,'op_id':'work-A','delta':1}

def encode(v):
    return json.dumps(v,sort_keys=True,separators=(',',':'))+'\n'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def snapshot(path):
    content = path.read_bytes()
    db = sqlite3.connect('file:'+quote(str(path.resolve()),safe='/')+'?mode=ro',uri=True)
    out = {name:[list(r) for r in db.execute('SELECT * FROM '+name+' ORDER BY 1,2')]
           for name in ['meta','receipts','effects']}
    db.close()
    out.update({'db_b64':base64.b64encode(content).decode(), 'db_sha256':sha(content)})
    return out

def invoke(db,command,calls):
    stdin = encode(command)
    argv = [sys.executable,'-B','-S',str(ROOT/'receiver.py'),str(db)]
    env = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
    started = time.monotonic_ns()
    p = subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    timed_out = False
    try:
        stdout,stderr = p.communicate(stdin.encode(),timeout=3)
    except subprocess.TimeoutExpired:
        timed_out = True
        p.kill()
        stdout,stderr = p.communicate(timeout=3)
    record = {'argv':argv,'stdin':stdin,'stdout':stdout.decode(),'stderr':stderr.decode(),
              'pid':p.pid,'returncode':p.returncode,'timeout':timed_out,
              'start_ns':started,'end_ns':time.monotonic_ns()}
    calls.append(record)
    if timed_out or p.returncode != 0 or stderr:
        raise RuntimeError('child failed: '+encode(record))
    result = json.loads(stdout)
    if result['pid'] != p.pid:
        raise ValueError('child identity mismatch')
    return result['result']

def run_case(out,scenario,policy,repetition):
    case = f'r{repetition}-{scenario}-{policy}'
    path = out/case
    path.mkdir()
    db = path/'state.sqlite'
    row = {'case_id':case,'scenario':scenario,'policy':policy,'repetition':repetition,'calls':[]}
    try:
        invoke(db,{'op':'init'},row['calls'])
        if scenario != 'RETIRED_NEVER_ACCEPTED':
            invoke(db,{'op':'execute','request':BASE},row['calls'])
        if scenario.startswith('RETIRED_') or scenario == 'FRESH_NEW_INTENT':
            invoke(db,{'op':'retire'},row['calls'])
        query = dict(BASE)
        if scenario.endswith('CHANGED_PAYLOAD'):
            query['delta'] = 2
        if scenario == 'FRESH_NEW_INTENT':
            query.update(epoch=8,op_id='work-B',delta=2)
        if scenario == 'WRONG_SESSION':
            query['session'] = 'foreign-session'
        if scenario == 'BOOLEAN_EPOCH':
            query['epoch'] = True
        row['request'] = query
        row['pre'] = snapshot(db)
        row['packet'] = invoke(db,{'op':'query','request':query},row['calls'])
        row['post_query'] = snapshot(db)
        row['decision'] = classify(row['packet'],query,policy)
        if row['decision']['submit']:
            row['recovery'] = invoke(db,{'op':'execute','request':query},row['calls'])
        else:
            row['recovery'] = None
        row['final'] = snapshot(db)
        row['status'] = 'COMPLETE'
    except Exception as exc:
        row['status'] = 'STOP'
        row['error'] = repr(exc)
        (path/'PARTIAL.json').write_text(encode(row))
        raise
    (path/'ROW.json').write_text(encode(row))
    return row

def source_check():
    frozen = json.loads((ROOT/'FREEZE.json').read_text())
    for name,expected in frozen['sources'].items():
        if sha((ROOT/name).read_bytes()) != expected:
            raise ValueError('source changed: '+name)
    env = json.loads((ROOT/'ENVIRONMENT.json').read_text())
    for path,expected in env['runtime_files'].items():
        if sha(Path(path).read_bytes()) != expected:
            raise ValueError('runtime changed: '+path)
    if sqlite3.sqlite_version != env['sqlite_version'] or sys.version != env['python']:
        raise ValueError('runtime version changed')
    return sha((ROOT/'FREEZE.json').read_bytes())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--batch',type=int,choices=range(3),required=True)
    parser.add_argument('--construction',action='store_true')
    args = parser.parse_args()
    args.out = args.out.resolve()
    if not args.construction and args.out != ROOT/'formal-01'/f'batch-{args.batch}':
        raise ValueError('formal output must match frozen canonical path')
    freeze = None if args.construction else source_check()
    if not args.construction and args.batch:
        prev = args.out.parent/f'batch-{args.batch-1}'
        receipt = json.loads((prev/'EXECUTION.json').read_text())
        if (type(receipt.get('returncode')) is not int or receipt['returncode'] != 0
            or receipt['timeout'] is not False or receipt['raw_sha256'] != sha((prev/'RAW.jsonl').read_bytes())):
            raise ValueError('previous batch not complete')
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/'CONSUMED.json').write_text(encode({'batch':args.batch,'construction':args.construction,
                                               'freeze_sha256':freeze,'pid':os.getpid()}))
    order = POLICIES if args.batch%2 == 0 else list(reversed(POLICIES))
    rows = 0
    with (args.out/'RAW.jsonl').open('x') as f:
        for scenario in SCENARIOS:
            for policy in order:
                row = run_case(args.out,scenario,policy,args.batch)
                f.write(encode(row)); f.flush(); os.fsync(f.fileno()); rows += 1
    if freeze is not None:
        source_check()
    print(encode({'status':'COMPLETE','rows':rows,'batch':args.batch,'freeze_sha256':freeze}),end='')

if __name__ == '__main__':
    main()
