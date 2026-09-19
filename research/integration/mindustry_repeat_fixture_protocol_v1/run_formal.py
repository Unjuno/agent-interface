#!/usr/bin/env python3
import json
from pathlib import Path
from protocol import Protocol,controller_projection
from coordinator import controller_accepts,next_private_actions
ROOT=Path(__file__).resolve().parent

def read(n): return json.loads((ROOT/n).read_text())
def dump(n,v): (ROOT/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def source_checks():
    js=(ROOT/'candidate_mod.js').read_text(); coord=(ROOT/'coordinator.py').read_text()
    return {
      'target_reset':'Vars.world.tile(137,52)' in js and 'target.setBlock(Blocks.air)' in js,
      'copper_exact_restore':'core.items.set(Items.copper,canonicalCopper)' in js,
      'score_pass_barrier':'score-pass-' in js and 'reset-' in js and 'phase=="awaitReset"' in js,
      'score_fail_stops':'score-fail-' in js and 'reset forbidden' in js,
      'private_dir_property':'agent.interface.benchmarkControlDir' in js,
      'controller_ops_only':"('submit','clock','cancel')" in coord and 'checkpoint' in coord and 'PRIVATE_OPS' in coord
    }

def good_trace(f):
    p=Protocol(f)
    for t in f['tasks']:
        assert p.task['task_id']==t['task_id']; assert p.checkpoint(t['epoch']); assert p.score(t['epoch'],True); assert p.reset(t['epoch'],True)
    return p

def controls(f):
    out={}
    p=Protocol(f); out['reset_before_score']=not p.reset(1,True)
    p=Protocol(f); p.checkpoint(1); p.score(1,False); out['failed_score_reset']=not p.reset(1,True) and p.phase=='stopped'
    p=Protocol(f); p.checkpoint(1); out['next_ready_before_witness']=not p.force_ready()
    p=Protocol(f); out['controller_checkpoint']=not p.controller('checkpoint'); out['controller_reset']=not p.controller('reset')
    p=Protocol(f); out['nonmonotonic_epoch']=not p.checkpoint(0)
    p=Protocol(f); p.checkpoint(1); p.score(1,True); out['bad_witness_stops']=not p.reset(1,False) and p.phase=='stopped'
    p=Protocol(f); p.checkpoint(1); out['duplicate_checkpoint']=not p.checkpoint(1)
    p=Protocol(f); p.checkpoint(1); p.score(1,True); p.reset(1,True); out['duplicate_reset']=not p.reset(1,True)
    return out

def main():
    s=ROOT/'.formal-invoked'
    if s.exists() or (ROOT/'RESULT.json').exists(): raise SystemExit('formal already invoked')
    s.write_text('1\n'); f=read('fixture.json'); p=good_trace(f); ctl=controls(f); src=source_checks(); proj=controller_projection(p.events,f)
    task_ready=[e for e in p.events if e['event']=='task_ready']; geom=[i for i,e in enumerate(p.events) if e['event']=='geometry_mutation']
    a3_reset=max(i for i,e in enumerate(p.events) if e.get('event')=='reset_witness' and e.get('epoch')==3)
    b1_ready=min(i for i,e in enumerate(p.events) if e.get('event')=='task_ready' and e.get('task_id')=='B1')
    private_names={'checkpoint_snapshot','score_verified','reset_applied','reset_witness','geometry_mutation','task_failed','reset_witness_failed'}
    gates={
      'source_checks':all(src.values()),
      'six_ready': [e['task_id'] for e in task_ready]==['A1','A2','A3','B1','B2','B3'],
      'geometry_once_between':len(geom)==1 and a3_reset < geom[0] < b1_ready,
      'complete':p.phase=='complete',
      'controls':all(ctl.values()),
      'projection_no_private':not any(e['event'] in private_names for e in proj),
      'projection_fields':all(set(e)<=set(f['controller_visible_keys']) for e in proj if e['event']=='task_ready'),
      'controller_private_ops_reject':not controller_accepts('checkpoint') and not controller_accepts('reset'),
      'coordinator_failure_no_reset':next_private_actions('A1',False,False)==['stop_failed_task'],
      'coordinator_a3_order':next_private_actions('A3',True,True)[-2:]==['geometry_mutation_A_to_B','publish_next_ready']
    }
    decision='PASS_MINDUSTRY_REPEAT_FIXTURE_PROTOCOL_SCOPED' if all(gates.values()) else 'FAIL_MINDUSTRY_REPEAT_FIXTURE_PROTOCOL'
    out={'schema':'mindustry_repeat_fixture_protocol_result_v1','task':'MINDUSTRY-REPEAT-FIXTURE-PROTOCOL-20260917-001','formal_invocation':1,'formal_reruns':0,'decision':decision,'gates':gates,'source_checks':src,'controls':ctl,'events':p.events,'controller_projection':proj,'scope':'source/protocol closure only; no live Mindustry/model/token/latency claim'}
    dump('RESULT.json',out); print(json.dumps({'decision':decision,'gates':gates},sort_keys=True)); raise SystemExit(0 if all(gates.values()) else 1)
if __name__=='__main__':main()
