import json,sys,time
from pathlib import Path
import vizdoom

OUT=Path(sys.argv[1]); OUT.parent.mkdir(parents=True,exist_ok=True)
strata=('idle','cpu_load','delayed_read'); rows=[]
def cpu_burn():
    x=0
    for i in range(250000): x=(x*1664525+i)&0xffffffff
    return x

for stratum in strata:
    game=vizdoom.DoomGame()
    game.load_config(str(Path(vizdoom.__file__).resolve().parent/'scenarios'/'basic.cfg'))
    game.set_window_visible(False); game.set_sound_enabled(False); game.set_render_hud(False)
    game.init(); game.new_episode()
    for sample in range(12):
        attempts=[]
        for attempt in range(3):
            game.advance_action(1)
            tic_before=int(game.get_episode_time()); start=time.monotonic_ns()
            if stratum=='cpu_load': cpu_burn()
            if stratum=='delayed_read': time.sleep(0.020)
            tic_after=int(game.get_episode_time()); finish=time.monotonic_ns()
            attempts.append({'attempt':attempt,'tic_before':tic_before,'tic_after':tic_after,'monotonic_start_ns':start,'monotonic_end_ns':finish,'span_ns':finish-start,'crossed_tic':tic_after>tic_before,'api_status':'ok'})
        rows.append({'stratum':stratum,'sample':sample,'attempts':attempts,'game_tic':int(game.get_episode_time()),'clock_hz':35})
    game.close()
OUT.write_text('\n'.join(json.dumps(r,sort_keys=True) for r in rows)+'\n')
print(json.dumps({'rows':len(rows),'strata':list(strata),'api':'vizdoom.get_episode_time'}))