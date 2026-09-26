"""Raw/SQLite verifier. Does not import policy, worker, peer or runner."""
from __future__ import annotations
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import sqlite3


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('DUPLICATE_JSON_KEY')
            result[k]=v
        return result
    return json.loads(path.read_bytes(),object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE')))


def audit_case(r, root, spec):
    errors=[]
    def check(condition,name):
        if not condition:errors.append(name)
    check(r['spec']==spec,'spec_identity')
    check(type(r['worker_pid']) is int and r['worker_pid']>0,'worker_pid_type')
    check(r['authority']=='none' and type(r['model_calls']) is int and r['model_calls']==0
          and type(r['gui_inputs']) is int and r['gui_inputs']==0,'authority_counts')
    check(r['cache_size']==(0 if spec['mode']=='NO_STATEMENT_CACHE' else 128),'cache_configuration')
    calls=r['peer_calls']; check(len(calls)==7,'peer_denominator')
    commands=['observe',spec['before'],'observe',spec['after'],'observe','observe','stop']
    outputs=[]
    for i,call in enumerate(calls):
        request=root/f'peer-{i:02}.request'; stdout=root/f'peer-{i:02}.stdout'
        q=load(request); x=load(stdout); outputs.append(x)
        check(sha(request)==call['request_sha256'] and sha(stdout)==call['stdout_sha256'],'peer_byte_binding')
        check(q=={'op_id':i,'command':commands[i]},'peer_request_order')
        check(type(x['op_id']) is int and x['op_id']==i and x['command']==commands[i],'peer_response_identity')
        check(type(x['pid']) is int and x['pid']==r['peer_process']['pid'] and x['pid']!=r['worker_pid'],'process_separation')
        check(all(type(t) is int for t in [call['started_ns'],call['finished_ns'],x['started_ns'],x['finished_ns']])
              and call['started_ns']<=x['started_ns']<=x['finished_ns']<=call['finished_ns'],'rpc_clock_order')
    check([r['initial'],r['before_operation'],r['before_prepare'],r['mutation'],r['after_mutation'],r['final'],r['peer_process']['terminal']]==outputs,'raw_rpc_consistency')
    pp=r['peer_process']; check(type(pp['returncode']) is int and pp['returncode']==0,'peer_exit')
    check(pp['terminal']['result']=={'status':'BYE'},'protocol_terminal')
    check(sha(root/'peer-process.stderr')==pp['stderr_sha256'] and not (root/'peer-process.stderr').read_bytes(),'peer_stderr')
    check(pp==load(root/'PEER_PROCESS.json'),'peer_process_file')
    p=r['prepared']; check(p==load(root/'PREPARED.json'),'prepared_retention')
    s0=r['initial']['result']; s1=r['before_prepare']['result']; s2=r['after_mutation']['result']; s3=r['final']['result']
    for state in (s0,s1,s2,s3):
        check(set(state['tables'])=={'a','b','u'},'table_set')
        check(all(type(pair[1]) is int and pair[1]>=1 and type(pair[0]) is str for pair in state['tables'].values()),'stored_version_type')
        check(type(state['schema_version']) is int,'schema_type')
    check(s0['tables']=={t:[spec['id']+':'+t+'0',1] for t in ('a','b','u')},'initial_values')
    check(s0['effects']==[],'initial_no_effect')
    def mutated(state,command):
        v=copy.deepcopy(state)
        if command.startswith('change_'):
            name=command[-1]; v['tables'][name][0]+='+changed';v['tables'][name][1]+=1
        if command=='retarget_b':
            v['view_sql']='CREATE VIEW current_view AS SELECT value FROM b';v['schema_version']+=2
        target='b' if v['view_sql'].endswith('FROM b') else 'a'
        v['view_value']=v['tables'][target][0]
        return v
    check(s1==mutated(s0,spec['before']),'before_mutation_truth')
    check(s2==mutated(s1,spec['after']),'after_mutation_truth')
    query=spec['sql']
    target='b' if query=='SELECT value FROM b' else (
        'b' if query=='SELECT value FROM current_view' and s1['view_sql'].endswith('FROM b') else 'a')
    check(p['sql']==query and p['sql_trace'].count(query)==1,'actual_select_trace')
    check(p['value']==s1['tables'][target][0],'prepared_value_from_actual_table')
    check(type(p['schema_version']) is int and p['schema_version']==s1['schema_version'],'prepared_schema')
    reads=[]
    for e in p['events']:
        check(type(e['action']) is int,'callback_action_type')
        if e['action']==20 and e['database']=='main' and e['first'] in ('a','b','u'):
            reads.append(e['first'])
    observed=sorted(set(reads))
    actual_names=[x['resource'] for x in p['receipts']]
    check(actual_names==sorted(set(actual_names)),'receipt_unique_sorted')
    for receipt in p['receipts']:
        name=receipt['resource']
        check(name in ('a','b','u') and type(receipt['revision']) is int and receipt['revision']==s1['tables'][name][1],'receipt_current_at_prepare')
    if spec['mode']!='METADATA_REUSE':check(actual_names==observed,'callback_collector_exact')
    else:
        check(actual_names==[target],'metadata_dep_reconstruction')
        if not observed:
            check(r['prime'] is not None and r['prime']['sql']==query
                  and r['prime']['schema_version']==p['schema_version'],'metadata_key_lineage')
            check(sorted({e['first'] for e in r['prime']['events'] if e['action']==20
                          and e['database']=='main' and e['first'] in ('a','b','u')})==actual_names,'metadata_origin_callback')
        else:check(actual_names==observed,'new_compile_replaces_metadata')
    current=(s1['schema_version']==s2['schema_version'] and
             s1['tables'][target][1]==s2['tables'][target][1])
    c=r['commit']; accepted=c['accepted']; check(type(accepted) is bool,'commit_boolean_type')
    check(c['schema_version']==s2['schema_version'],'commit_schema_truth')
    check(c['versions_checked']=={x['resource']:s2['tables'][x['resource']][1] for x in p['receipts']},'commit_checked_versions')
    calculated=(p['status']=='PREPARED' and p['schema_version']==s2['schema_version'] and
                all(s2['tables'][x['resource']][1]==x['revision'] for x in p['receipts']))
    check(accepted==calculated,'commit_algorithm_reconstruction')
    expected=copy.deepcopy(s2);expected['effects']=[[spec['id'],p['value']]] if accepted else []
    check(s3==expected,'actual_committed_effect')
    check(sha(root/'state.sqlite')==r['database_sha256'],'database_digest')
    con=sqlite3.connect((root/'state.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    try:
        tables={name:list(con.execute(f'SELECT value,revision FROM {name}').fetchone()) for name in ('a','b','u')}
        effects=[list(x) for x in con.execute('SELECT request_id,payload FROM effects ORDER BY request_id')]
        check(tables==s3['tables'] and effects==s3['effects'],'readonly_database_reconstruction')
        check(con.execute('PRAGMA integrity_check').fetchone()==('ok',),'sqlite_integrity')
    finally:con.close()
    check(outputs[2]['finished_ns']<=r['prepare_bracket_ns'][0]<=r['prepare_bracket_ns'][1]<=outputs[3]['started_ns'],'prepare_writer_order')
    check(outputs[4]['finished_ns']<=r['commit_bracket_ns'][0]<=r['commit_bracket_ns'][1]<=outputs[5]['started_ns'],'writer_commit_order')
    return errors,{'cases':1,'commits':int(accepted),'stale_commits':int(accepted and not current),
        'false_refusals':int(not accepted and current),'missing_dependencies':int(target not in actual_names),
        'metadata_reuses':int(p['metadata_origin']=='CONNECTION_SCHEMA_SQL_METADATA'),
        'read_callback_events':len(reads)}


def audit(root, here, construction=False):
    errors=[];stats={};cases=[]
    planned=load(here/'SCHEDULE.json')
    if construction: planned=[dict(s,id='build-'+s['id']) for s in planned[:30]]
    if not construction:
        f=load(here/'FREEZE.json')
        errors += ['source:'+n for n,d in f['sources'].items() if sha(here/n)!=d]
    previous=None
    for bi,start in enumerate(range(0,len(planned),6)):
        b=root/f'batch-{bi:02d}'; e=load(b/'EXECUTION.json')
        if e['range']!=[start,min(start+6,len(planned))] or e['status']!='COMPLETE':errors.append('batch_range_or_status')
        if e['previous_execution_sha256']!=previous:errors.append('batch_chain')
        previous=sha(b/'EXECUTION.json')
        outer=load(root/f'OUTER-{bi:02d}.json')
        if type(outer['returncode']) is not int or outer['returncode']!=0:errors.append('outer_exit')
        if outer['execution_sha256']!=previous:errors.append('outer_binding')
        if outer['stdout_sha256']!=sha(root/f'OUTER-{bi:02d}.stdout'):errors.append('outer_stdout_binding')
        if outer['stderr_sha256']!=sha(root/f'OUTER-{bi:02d}.stderr'):errors.append('outer_stderr_binding')
        for expected,w in zip(planned[start:start+6],e['workers'],strict=True):
            try:
                if w['id']!=expected['id'] or type(w['returncode']) is not int or w['returncode']!=0:errors.append('worker_exit_or_identity')
                r=load(b/w['id']/'RAW.json');stdout=b/(w['id']+'.stdout');stderr=b/(w['id']+'.stderr')
                if sha(stdout)!=w['stdout_sha256'] or sha(stderr)!=w['stderr_sha256'] or stderr.read_bytes():errors.append('worker_stdio')
                if load(stdout)!={'id':expected['id'],'raw_sha256':sha(b/w['id']/'RAW.json')}:errors.append('worker_raw_binding')
                er,st=audit_case(r,b/w['id'],expected); errors.extend([expected['id']+':'+x for x in er])
                mode=expected['mode'];stats.setdefault(mode,collections.Counter()).update(st)
                cases.append({'id':expected['id'],'condition':expected['condition'],'mode':mode,**st})
            except (KeyError,ValueError,TypeError,OSError,sqlite3.Error) as ex:
                errors.append(expected['id']+':'+type(ex).__name__+':'+str(ex))
    gates=[]
    reps=1 if construction else 2
    for mode in ('NO_STATEMENT_CACHE','METADATA_REUSE'):
        tested=('stale_commits','missing_dependencies') if mode=='NO_STATEMENT_CACHE' else ('stale_commits','false_refusals','missing_dependencies')
        if any(stats[mode][k] for k in tested):gates.append(mode+':freshness_or_precision')
    if stats['EVENT_ONLY']['stale_commits']!=reps or stats['EVENT_ONLY']['missing_dependencies']!=5*reps:gates.append('compile_event_boundary_not_exposed')
    if stats['METADATA_REUSE']['metadata_reuses']!=5*reps:gates.append('metadata_cache_reuse_not_exposed')
    return {'audit_pass':not errors,'errors':errors,'scientific_gate_failures':gates,
            'decision':('PASS_SQLITE_READSET_CACHE_BOUNDARY_SCOPED' if not errors and not gates else
                        'HOLD_EVIDENCE_INCOMPLETE' if errors else 'FAIL_BOUNDARY_HYPOTHESIS'),
            'construction':construction,'case_count':len(cases),'summary':{k:dict(v) for k,v in stats.items()},'cases':cases}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--out',required=True);p.add_argument('--construction',action='store_true');a=p.parse_args()
    result=audit(Path(a.root),Path(__file__).resolve().parent,a.construction)
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2,sort_keys=True))
    raise SystemExit(0 if result['audit_pass'] and not result['scientific_gate_failures'] else 1)
