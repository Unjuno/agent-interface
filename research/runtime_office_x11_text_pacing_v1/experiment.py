#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
PORTABLE=Path(os.environ['AGENT_INTERFACE_PORTABLE_ORACLE'])
X11=Path(os.environ['AGENT_INTERFACE_X11_BACKEND'])
OFFICE=Path(os.environ['AGENT_INTERFACE_OFFICE_V0'])
sys.path[:0]=[str(PORTABLE),str(X11),str(OFFICE)]
from contract import OFFICE_FLOOR, admit_program, capability_manifest
from office_backend import OfficeX11Backend

CORPUS=['office','coffee','bookkeeper','committee','parallel','address','success','letterpress','mississippi','assessment','committee','bookkeeping','ffffffffff','aaaaaaaaaa','tttttttttt','ssssssssss']

def make_program(pid,seq,revision,expires,ops):
    if ops[-1].get('op')!='release_all': ops=list(ops)+[{'op':'release_all'}]
    return {'schema':'agent-interface/program-v0','program_id':pid,'source':{'observation_seq':seq,'binding_revision':revision},'authority':{'lease_id':'calc-pacing-v1','expires_at_ns':expires},'ops':ops,'terminal':{'release_all_required':True}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--display',required=True); ap.add_argument('--window-id',type=int,required=True); ap.add_argument('--pacing-ms',type=float,required=True); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    backend=OfficeX11Backend(a.display,{'calc':a.window_id},text_pacing_s=a.pacing_ms/1000.0)
    manifest=capability_manifest('office-x11-pacing-v1','linux','x11',OFFICE_FLOOR,frames=('screen_physical_px','window_client'))
    now=time.monotonic_ns(); future=now+60_000_000_000
    stale=make_program('pacing-stale',4,1,future,[{'op':'focus','target':'calc'},{'op':'text','text':'x'},{'op':'release_all'}])
    before=backend.emissions
    sa=admit_program(stale,manifest,now_ns=time.monotonic_ns(),current_observation_seq=5,current_binding_revision=1)
    after=backend.emissions
    ops=[{'op':'focus','target':'calc'},{'op':'pointer_move','frame':'window_client','x':80,'y':180},{'op':'pointer_button','button':'left','down':True},{'op':'pointer_button','button':'left','down':False},{'op':'key_chord','keys':['CTRL','Home']}]
    for text in CORPUS:
        ops += [{'op':'text','text':text},{'op':'key_chord','keys':['ENTER']}]
    ops += [{'op':'key_chord','keys':['CTRL','S']},{'op':'wait_update','timeout_ms':400},{'op':'key_chord','keys':['ENTER']},{'op':'wait_update','timeout_ms':1200},{'op':'release_all'}]
    task=make_program(f'pacing-{int(a.pacing_ms*1000)}us',5,1,future,ops)
    adm=admit_program(task,manifest,now_ns=time.monotonic_ns(),current_observation_seq=5,current_binding_revision=1)
    t0=time.perf_counter_ns(); execution=backend.execute(task) if adm.accepted else None; t1=time.perf_counter_ns()
    release=bool(execution and execution['releases'] and execution['releases'][-1]['verified'] and execution['releases'][-1]['keys_down']==[] and execution['releases'][-1]['buttons_down']==[])
    result={'schema':'agent-interface/office-x11-text-pacing-execution-v1','pacing_ms':a.pacing_ms,'corpus':CORPUS,'stale':{'accepted':sa.accepted,'error':sa.error,'emissions_before':before,'emissions_after':after},'task_admission':{'accepted':adm.accepted,'error':adm.error},'backend_emissions':backend.emissions,'release_verified':release,'task_elapsed_ns':t1-t0}
    result['passed_transport']=(not sa.accepted and sa.error=='STALE_OBSERVATION' and before==after and adm.accepted and release)
    (a.out/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
    backend.close(); print(json.dumps(result,indent=2)); return 0 if result['passed_transport'] else 1
if __name__=='__main__': raise SystemExit(main())
