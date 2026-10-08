from __future__ import annotations
import glob, hashlib, json, os, resource, struct, sys, time
from pathlib import Path
import vizdoom as vd

WAD=Path('/assets/freedoom2.wad')
OUT=Path('/results/raw.jsonl')
TRACE=Path('/tmp/vizdoom-tic-counter-v1.bin')
EXPECTED_WAD='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
ENTRY=struct.Struct('=QQQii')

def main():
    arm=sys.argv[1]; pair=int(sys.argv[2]); expected='instrumented' if arm=='instrumented' else 'control'
    if arm not in ('instrumented','control'): raise SystemExit('STOP_BAD_ARM')
    exe=Path(vd.__file__).parent/'vizdoom'
    import subprocess
    dis=subprocess.check_output(['objdump','-d',str(exe)],text=True,stderr=subprocess.STDOUT)
    hits=dis.count('mrs\tx0, cntvct_el0')+dis.count('mrs x0, cntvct_el0')
    if expected=='instrumented' and hits!=1: raise SystemExit(f'STOP_INSTRUMENTED_OPCODE_COUNT_{hits}')
    if expected=='control' and hits!=0: raise SystemExit(f'STOP_CONTROL_HAS_COUNTER_OPCODE_{hits}')
    if hashlib.sha256(WAD.read_bytes()).hexdigest()!=EXPECTED_WAD: raise SystemExit('STOP_WAD_HASH')
    TRACE.unlink(missing_ok=True)
    g=vd.DoomGame(); row={'schema':'issue3453-construction-clock49-v1','arm':arm,'pair':pair,
      'engine_binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
      'wad_sha256':hashlib.sha256(WAD.read_bytes()).hexdigest(),'counter_opcode_hits':hits,
      'setup_status':'not_started','cleanup':{'game_closed':False}}
    try:
        g.set_doom_game_path(str(WAD)); g.set_doom_map('map01'); g.set_window_visible(False); g.set_sound_enabled(False)
        g.set_mode(vd.Mode.ASYNC_SPECTATOR); g.set_ticrate(35); g.set_available_buttons([]); g.set_episode_timeout(350); g.set_seed(349000+pair); g.init(); g.new_episode()
        row['setup_status']='ok'; row['mode']=str(g.get_mode()); row['ticrate']=int(g.get_ticrate())
        reads=0; api_tics=[]; wall0=time.monotonic_ns(); cpu0=time.process_time_ns()
        deadline=time.monotonic()+6.0
        while time.monotonic()<deadline:
            api_tics.append(int(g.get_episode_time())); reads+=1; time.sleep(.01)
        cpu1=time.process_time_ns(); wall1=time.monotonic_ns()
        row.update({'wall_ns':wall1-wall0,'process_cpu_ns':cpu1-cpu0,'cpu_wall_ratio':(cpu1-cpu0)/(wall1-wall0),
                    'passive_read_count':reads,'api_tic_values':sorted(set(api_tics))})
    except BaseException as e:
        row['setup_status']='STOP_SETUP_OR_INFRA'; row['error']={'type':type(e).__name__,'message':str(e)}
    finally:
        try: g.close(); row['cleanup']['game_closed']=True
        except BaseException as e: row['cleanup_error']={'type':type(e).__name__,'message':str(e)}
        if TRACE.exists():
            b=TRACE.read_bytes(); row['trace_sha256']=hashlib.sha256(b).hexdigest()
            if len(b)%ENTRY.size: row['trace_error']='partial_record'
            else:
                rows=[ENTRY.unpack_from(b,i) for i in range(0,len(b),ENTRY.size)]
                row['engine_entry_count']=len(rows)
                row['engine_viz_time_range']=[min(x[4] for x in rows),max(x[4] for x in rows)] if rows else []
                row['counter_frequency_hz']=rows[0][2] if rows else None
                row['engine_viztime_rate_hz']=(max(x[4] for x in rows)-min(x[4] for x in rows))*1e9/(wall1-wall0) if len(rows)>1 else None
        with OUT.open('a') as f: f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
        print(json.dumps(row,sort_keys=True))
if __name__=='__main__': main()
