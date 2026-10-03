"""Saved-only verification of retained first readiness STOP. No native calls."""
import hashlib
import json
from pathlib import Path
import audit

def main():
    here = Path(__file__).resolve().parent
    root = here / 'construction-01'
    raw = audit.read(root/'record/raw.json')
    audit.need(raw['mode'] == 'construction' and raw['status'] == 'STOP', 'excluded first STOP')
    audit.join(raw['started_cells'], ['construction-dark','construction-persistent','construction-pulse'], '3 cells started')
    audit.join(raw['cells'], ['construction-dark','construction-persistent'], '2 cells qualified')
    audit.join(raw['cgroups'], {'cpu.max':'100000 100000','memory.max':'536870912',
                              'memory.swap.max':'0','pids.max':'64'}, 'actual native limits')
    for name,digest in raw['source_sha256'].items():
        audit.need(hashlib.sha256((root/'staged-source'/name).read_bytes()).hexdigest() == digest, 'executed source pin '+name)
    launch = audit.read(root/'launch.json')
    state = json.loads(launch['inspect_stdout'])
    audit.need(launch['exit_code'] == 2 and launch['inspect_exit'] == 0, 'terminal native exit2')
    audit.need(state['State']['ExitCode'] == 2 and not state['State']['Running'] and not state['State']['OOMKilled'], 'terminal noOOM')
    audit.need(type(state['RestartCount']) is int and state['RestartCount'] == 0, 'restart0')
    audit.need(state['Image'] == 'sha256:c4839671ed0625dd38a53d8ed542bab16407c2b4c88a5ac84431695438c2b816', 'native image')
    audit.need(audit.read(root/'copy.json')['exit_code'] == 0, 'retained native outputs')
    host = state['HostConfig']
    audit.join({k:host[k] for k in ('NanoCpus','Memory','MemorySwap','PidsLimit','NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt')},
               {'NanoCpus':1000000000,'Memory':536870912,'MemorySwap':536870912,'PidsLimit':64,
                'NetworkMode':'none','ReadonlyRootfs':True,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges']}, 'inspected isolation')
    audit.join([(m['Source'],m['Destination'],m['RW']) for m in state['Mounts']],
               [('/home/taka/inputs/phase-effect-a02-3cbf-construction-v1','/src',False),
                ('/home/taka/outputs/phase-effect-a02-3cbf-construction-v1','/out',True)], 'owned source/output mounts')
    captures = 0
    for name in raw['started_cells']:
        cell = root/'record/cells'/name
        saved = audit.read(cell/'cell.json')
        for filename,digest in saved['files_sha256'].items():
            audit.need(hashlib.sha256((cell/filename).read_bytes()).hexdigest() == digest, 'raw hash '+filename)
        so,ca = audit.read(cell/'source.json'),audit.read(cell/'capture.json')
        audit.join([audit.parse_record(x) for x in (cell/'frames.jsonl').read_text().splitlines()], ca['frames'], 'native frames journal')
        captures += len(ca['frames'])
        if name != 'construction-pulse':
            audit.audit_cell(saved['spec'],so,ca,saved['lifecycle'])
        else:
            try: audit.audit_cell(saved['spec'],so,ca,saved['lifecycle'])
            except ValueError as error: audit.need(str(error) == 'rendered exposure','same first scientific gate')
            else: raise ValueError('pulse STOP disappeared')
            event = so['events'][0]
            audit.need(event['clear_start_ns']-event['draw_end_ns'] == 14_147_484, 'exact first exposure')
    audit.need(captures == 24, 'actual saved denominator24')
    print(json.dumps({'retention':'PASS','construction_status':'STOP_READINESS_SOURCE_EXPOSURE',
                      'started_cells':3,'qualified_cells':2,'captures':24,
                      'declared_history': {'formal_producer_invocations':0,
                                           'official_scientific_auditor_invocations':0}},sort_keys=True))

if __name__ == '__main__': main()
