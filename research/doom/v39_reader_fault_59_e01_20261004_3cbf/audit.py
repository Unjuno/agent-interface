"""Saved-only diagnostic audit; intentionally independent of core.judge."""
import hashlib
import ast
import json
import os
import pathlib
import sys

SOURCE_HASH='a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e'
PAYLOADS={'healthy': b'{"event":"ready","fixture":"synthetic"}\n',
          'malformed':b'not-json\n','array':b'[]\n'}

def closed_object(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key]=value
    return result

def check(root, source_path=None):
    def read(name):
        p=root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError('nonregular receipt '+name)
        return json.loads(p.read_bytes(),object_pairs_hook=closed_object)
    summary=read('SUMMARY.json')
    if summary['source']['sha256'] != SOURCE_HASH:
        raise ValueError('wrong source')
    if source_path is not None:
        source=source_path.read_bytes()
        tree=ast.parse(source.decode())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        nodes=[n for n in main.body if isinstance(n,ast.FunctionDef) and n.name in ('reader','wait')]
        identity=dict(sha256=hashlib.sha256(source).hexdigest(),functions=[n.name for n in nodes],
            ast_sha256=hashlib.sha256(ast.dump(ast.Module(body=nodes,type_ignores=[])).encode()).hexdigest())
        if summary['source'] != identity: raise ValueError('AST identity')
    runtime=read('RUNTIME.json')
    if type(runtime['pid']) is not int or runtime['pid']<=0 or runtime['uid']!=501 or runtime['limits'] != {'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}:
        raise ValueError('runtime allocation')
    rows=[]
    expected=[('healthy','ready',True,[]),('malformed','TimeoutError',False,['JSONDecodeError']),
              ('array','TypeError',True,[])]
    for case,outcome,alive,errors in expected:
        row=read(case+'-result.json')
        peer=read(case+'-peer.json')
        if row['case'] != case or type(row['pid']) is not int or row['pid'] != peer['pid'] or peer['ppid'] != row['producer_pid'] or row['producer_pid'] != runtime['pid']:
            raise ValueError('peer identity')
        if peer['emitted_hex'] != PAYLOADS[case].hex() or type(peer['written']) is not int or peer['written'] != len(PAYLOADS[case]):
            raise ValueError('wrong emitter payload')
        if row.get('fatal') or row.get('cleanup_faults') or type(row['reader_alive']) is not bool or row['child_alive'] is not True or type(row['cleanup_exit']) is not int or row['cleanup_exit'] != 0 or row['reader_retired'] is not True:
            raise ValueError('custody cleanup')
        rows.append(row)
    if rows != summary['rows']:
        raise ValueError('summary rows disagree')
    finding=all((r['outcome'],r['reader_alive'],r['errors'])==(o,a,e)
                for r,(_,o,a,e) in zip(rows,expected))
    if finding:
        if len(rows[1]['error_details'])!=1 or rows[1]['error_details'][0]['doc'] != 'not-json\n' or rows[1]['error_details'][0]['type']!='JSONDecodeError' or rows[1]['error_details'][0]['thread']!='v39-reader-malformed':
            raise ValueError('parse input')
        if rows[0]['parsed_events'] != [{'event':'ready','fixture':'synthetic'}] or rows[1]['parsed_events'] != [] or rows[2]['parsed_events'] != [[]]:
            raise ValueError('parsed event shape')
    verdict='FINDING_PARSE_FAILURE_NOT_SURFACED' if finding else 'HOLD_EXPECTATION_NOT_MET'
    if summary['verdict'] != verdict or summary['source'] != read('source-identity.json'):
        raise ValueError('verdict identity')
    return verdict

if __name__=='__main__':
    root=pathlib.Path(sys.argv[1])
    output=pathlib.Path(sys.argv[2])
    output.mkdir(parents=True,exist_ok=False)
    try:
        result=dict(status='PASS_SAVED_DIAGNOSTIC_AUDIT',verdict=check(root,pathlib.Path(__file__).parent/'source/v39.py.txt'),uid=os.getuid(),
                    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir()) if p.is_file()})
        code=0
    except Exception as exc:
        result=dict(status='FAIL_SAVED_DIAGNOSTIC_AUDIT',error=repr(exc),uid=os.getuid())
        code=1
    (output/'AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result))
    sys.exit(code)
