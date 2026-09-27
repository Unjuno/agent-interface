from __future__ import annotations
import hashlib,importlib.util,json,re,struct,subprocess,time
from pathlib import Path
import vizdoom as vd
import sys
sys.path.insert(0,'/scorer')

WAD=Path('/assets/freedoom2.wad'); SCORER=Path('/scorer/session_map01_v13.py'); TRACE=Path('/tmp/vizdoom-tic-counter-v1.bin'); OUT=Path('/results/raw.json')
EXPECTED_WAD='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
RECORD=struct.Struct('=QQQii')
GETTERS={'get_episode_time','is_episode_finished','is_player_dead','get_game_variable','get_ticrate','is_episode_timeout_reached'}

def load_counter():
    candidates=list(Path('/').glob('counter_call*.so'))
    if len(candidates)!=1: raise RuntimeError(f'counter extension count={len(candidates)}')
    spec=importlib.util.spec_from_file_location('counter_call',candidates[0]); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def verify_disassembly():
    obj=Path('/opt/vizdoom-counter-audit/viz_main.cpp.o')
    exe=Path(vd.__file__).parent/'vizdoom'
    if not obj.is_file() or not exe.is_file(): raise RuntimeError('STOP_ENGINE_ARTIFACT_NOT_FOUND')
    objdump=subprocess.check_output(['objdump','-drC',str(obj)],text=True,stderr=subprocess.STDOUT)
    lines=objdump.splitlines(); start=next((i for i,line in enumerate(lines) if re.search(r'<VIZ_Tic\(\)>:',line)),None)
    if start is None: raise RuntimeError('STOP_ENTRY_SYMBOL_NOT_FOUND')
    instructions=[]; relocation=False
    for line in lines[start+1:]:
        if re.search(r'<[^>]+>:',line): break
        if re.search(r'R_AARCH64_JUMP26\s+VIZ_TicCounterBody',line): relocation=True
        if re.match(r'\s*[0-9a-f]+:',line): instructions.append(line.strip())
        if len(instructions)==2 and relocation: break
    if not instructions or not re.search(r'\bmrs\s+x0,\s*cntvct_el0\b',instructions[0]):
        raise RuntimeError('STOP_OBJECT_FIRST_MACHINE_INSTRUCTION_NOT_CNTVCT: '+repr(instructions))
    if len(instructions)<2 or not re.search(r'\bb\s',instructions[1]) or not relocation:
        raise RuntimeError('STOP_OBJECT_ENTRY_BRANCH_NOT_IMMEDIATE: '+repr(instructions))
    linked=subprocess.check_output(['objdump','-d',str(exe)],text=True,stderr=subprocess.STDOUT).splitlines()
    hits=[i for i,line in enumerate(linked) if re.search(r'\bmrs\s+x0,\s*cntvct_el0\b',line)]
    if len(hits)!=1 or hits[0]+1>=len(linked) or not re.search(r'\bb\s',linked[hits[0]+1]):
        raise RuntimeError('STOP_LINKED_ENTRY_OPCODE_OR_BRANCH_MISMATCH: '+repr([linked[i:i+2] for i in hits]))
    return {'object':instructions[:2],'object_relocation_to_body':True,'linked_binary':linked[hits[0]:hits[0]+2]}

class TimedProxy:
    def __init__(self,g,counter): self.g=g; self.counter=counter; self.events=[]
    def __getattr__(self,n):
        f=getattr(self.g,n)
        if n not in GETTERS or not callable(f): return f
        def call(*args,**kwargs):
            result,lo,hi=self.counter.call_timed(f,args,kwargs or None)
            value=getattr(result,'name',result)
            self.events.append({'name':n,'args':[repr(x) for x in args],'counter_lower':lo,'counter_upper':hi,'result':value,'status':'ok'})
            return result
        return call

def get_tic(g,counter):
    tic,lo,hi=counter.call_timed(g.get_episode_time,(),None)
    return {'counter_lower':lo,'counter_upper':hi,'tic':int(tic)}

def main():
    counter=load_counter(); freq=int(counter.read_frequency()); sample=int(counter.read_counter())
    if freq<=0: raise SystemExit('STOP_COUNTER_FREQUENCY_INVALID')
    disasm=verify_disassembly()
    if sys.argv[1:]==['--preflight-only']:
        print(json.dumps({'preflight':'PASS_NO_GAME_STARTED','counter_frequency_hz':freq,'counter_sample':sample,'entry_disassembly':disasm},sort_keys=True)); return
    from session_map01_v13 import _coherent_progress_sample
    if hashlib.sha256(WAD.read_bytes()).hexdigest()!=EXPECTED_WAD or not SCORER.is_file(): raise SystemExit('STOP_INPUT_IDENTITY')
    rows=[]
    for i in range(3):
        TRACE.unlink(missing_ok=True); g=vd.DoomGame(); r={'schema':'issue3453-construction-clock48-v1','index':i,'setup_status':'not_started','counter_frequency_hz':freq,'counter_preflight_sample':sample,'entry_disassembly':disasm,'scorer_sha256':hashlib.sha256(SCORER.read_bytes()).hexdigest(),'wad_sha256':hashlib.sha256(WAD.read_bytes()).hexdigest(),'cleanup':{'game_closed':False}}
        try:
            g.set_doom_game_path(str(WAD)); g.set_doom_map('map01'); g.set_window_visible(False); g.set_sound_enabled(False); g.set_mode(vd.Mode.ASYNC_SPECTATOR); g.set_ticrate(35); g.set_available_buttons([]); g.set_episode_timeout(350); g.set_seed(345800+i); g.init(); g.new_episode()
            r['setup_status']='ok'; r['mode']=str(g.get_mode()); r['ticrate']=int(g.get_ticrate()); r['passive_reads']=[]
            deadline=time.monotonic()+1.5
            while time.monotonic()<deadline: r['passive_reads'].append(get_tic(g,counter)); time.sleep(.01)
            r['scorer_start_counter']=int(counter.read_counter()); proxy=TimedProxy(g,counter)
            try: r['scorer_return']=_coherent_progress_sample(proxy,vd.GameVariable,10.0).as_dict(); r['scorer_status']='returned'
            except BaseException as e: r['scorer_status']='raised'; r['scorer_error']={'type':type(e).__name__,'message':str(e)}
            r['scorer_getters']=proxy.events; r['scorer_end_counter']=int(counter.read_counter())
            r['post_passive_start_counter']=int(counter.read_counter()); time.sleep(.25); r['post_passive_end_counter']=int(counter.read_counter())
        except BaseException as e: r['setup_status']='STOP_SETUP_OR_INFRA'; r['error']={'type':type(e).__name__,'message':str(e)}
        finally:
            try: g.close(); r['cleanup']['game_closed']=True
            except BaseException as e: r['cleanup_error']={'type':type(e).__name__,'message':str(e)}
            if TRACE.exists():
                data=TRACE.read_bytes()
                if len(data)%RECORD.size: r['trace_error']='partial_record'
                else: r['tic_entry_records']=[dict(zip(('counter','monotonic_ns_after_entry','counter_frequency_hz','gametic','viz_time'),RECORD.unpack_from(data,j))) for j in range(0,len(data),RECORD.size)]; r['trace_sha256']=hashlib.sha256(data).hexdigest()
            rows.append(r)
            with OUT.open('a') as f: f.write(json.dumps(r,sort_keys=True)+'\n'); f.flush()
    OUT.write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(rows),'frequency_hz':freq,'entry_disassembly':disasm,'setup_ok':sum(x['setup_status']=='ok' for x in rows),'scorer_returned':sum(x.get('scorer_status')=='returned' for x in rows),'closed':sum(x['cleanup']['game_closed'] for x in rows)},sort_keys=True))

if __name__=='__main__': main()
