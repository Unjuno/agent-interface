"""A03 prospective readiness and formal selection, closed modes."""
import re
import hashlib
from reference import parse_record
from reference import check_fixture_plan, join, need

READINESS_ALLOCATION='PHASE-EFFECT-6067-A03-READINESS-20261004-3CBF'
REQUIRED_SOURCE={'audit_commands.py','audit_runner.py','cell_validation.py','common.py','controls.py','decision.py',
                 'evidence.py','fixture.py','fixture.json','mount_adapter.py','observer.py','policy.py',
                 'producer.py','protocol.py','qualification.py','reference.py','runner.py','saved_audit.py',
                 'timing.py','tree_custody.py','x11.py'}
CONTROL_NAMES={'wait_bool','cpu_false','missing_wait','post_after_paint','source_wait_id','pixel_hash',
               'source_journal_id','observer_wait_index','duplicate','wrong_source','wrong_rw','missing',
               'extra','nonbind','bool_rw'}
SUPPLEMENTAL_SOURCE={'README.md','STATUS_SNAPSHOT.md','test_audit_commands.py','test_audit_state.py','test_cell_validation.py',
                     'test_custody_mode.py','test_decision.py','test_freeze_bytes.py','test_protocol.py','test_qualification.py',
                     'test_saved_controls.py','test_tree_custody.py'}
SUPPLEMENTAL_SOURCE.add('test_output_layout.py')

def freeze_filename(mode,name=None):
    need(mode in ('readiness','formal'),'closed freeze mode')
    name=name or mode+'-FREEZE.json'
    need(type(name) is str and re.fullmatch(mode+r'(-v[1-9][0-9]*)?-FREEZE\.json',name) is not None,
         'closed explicit stage freeze filename')
    return name

def cases_for(mode, fixture):
    check_fixture_plan(fixture)
    if mode == 'formal':
        return fixture['cases']
    need(mode == 'readiness', 'closed execution mode')
    specs=[{'id':'r000','kind':'dark','schedule':'fixed','offsets':[0]*4},
           {'id':'r001','kind':'persistent','schedule':'fixed','offsets':[0]*4}]
    for i,width in enumerate((10,20,30),2):
        specs.append({'id':f'r{i:03}','kind':'pulse','schedule':'fixed',
                      'offsets':[0]*4,'phase':0,'width_ms':width})
    return specs

def admit_stage(freeze, mode, source_sha256, fixture, readiness_bytes=None):
    cases_for(mode, fixture)
    join(freeze['mode'],mode,'stage mode')
    allocation=READINESS_ALLOCATION if mode == 'readiness' else fixture['allocation']
    join(freeze['allocation'],allocation,'stage allocation')
    join(freeze['source_sha256'],source_sha256,'frozen source set')
    need(type(source_sha256) is dict and bool(source_sha256),'nonempty source pins')
    need(REQUIRED_SOURCE <= set(source_sha256),'complete execution dependency pins')
    for name in source_sha256:
        need(name in REQUIRED_SOURCE or name in SUPPLEMENTAL_SOURCE or
             (name.startswith('construction-methods/') and name.endswith(('.log','.json','.md'))),
             'declared supplemental source or construction evidence')
    for name,digest in source_sha256.items():
        need(type(name) is str and not name.startswith('/') and '..' not in name.split('/'), 'source relative path')
        need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None,'source digest')
    if mode == 'formal':
        r=freeze.get('qualified_readiness',{})
        need(r.get('status') == 'PASS_READINESS_SCOPED', 'independent readiness qualification')
        need(r.get('allocation') == READINESS_ALLOCATION, 'readiness allocation identity')
        digest=r.get('result_sha256')
        need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None,
             'readiness result hash')
        need(type(readiness_bytes) is bytes and hashlib.sha256(readiness_bytes).hexdigest()==digest,
             'qualified readiness artifact bytes')
        result=parse_record(readiness_bytes.decode('utf-8'))
        join({k:result[k] for k in ('status','allocation','mode','cells','captures','input_events','model_calls')},
             {'status':'PASS_READINESS_SCOPED','allocation':READINESS_ALLOCATION,'mode':'readiness',
              'cells':5,'captures':40,'input_events':0,'model_calls':0},'readiness actual full stage')
        join(result['source_sha256'],source_sha256,'same qualified readiness source')
        controls=result['controls']
        need(type(controls) is list and len(controls)==15,'all fifteen readiness controls')
        need({c['name'] for c in controls}==CONTROL_NAMES and all(c['rejected'] is True for c in controls),
             'all unique saved controls rejected')
        join(result['auditor_cgroups'],{'cpu.max':'100000 100000','memory.max':'536870912',
                                       'memory.swap.max':'0','pids.max':'64'},'actual readiness auditor cgroups')
        specs=cases_for('readiness',fixture)
        need(type(result['rows']) is list and len(result['rows'])==5,'readiness five rows')
        for spec,row in zip(specs,result['rows']):
            join({k:row[k] for k in spec},spec,'qualified readiness ordered spec')
            expected=[] if spec['kind']=='dark' else [1] if spec['kind']=='persistent' else list(range(1,9))
            join(row['stable_ids'],expected,'qualified readiness stable IDs')
            join([row['boundary_hits'],row['unknown_frames'],row['captures_checked']],[0,0,8],
                 'qualified readiness clean captures')
