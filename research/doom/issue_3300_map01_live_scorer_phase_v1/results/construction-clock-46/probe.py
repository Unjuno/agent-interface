from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import vizdoom as vd
sys.path.insert(0, '/scorer')
from session_map01_v13 import _coherent_progress_sample

WAD = Path('/assets/freedoom2.wad')
SCORER = Path('/scorer/session_map01_v13.py')
OUT = Path('/results/raw.jsonl')
EXPECTED_WAD = 'a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
GETTERS = {'get_episode_time', 'is_episode_finished', 'is_player_dead', 'get_game_variable', 'get_ticrate', 'is_episode_timeout_reached'}

class TimedProxy:
    def __init__(self, game):
        self.inner, self.events = game, []
    def __getattr__(self, name):
        value = getattr(self.inner, name)
        if name not in GETTERS or not callable(value):
            return value
        def call(*args, **kwargs):
            start = time.monotonic_ns()
            try:
                result = value(*args, **kwargs)
            except BaseException as exc:
                self.events.append({'name':name,'start_ns':start,'end_ns':time.monotonic_ns(),'status':'error','error_type':type(exc).__name__})
                raise
            end = time.monotonic_ns()
            self.events.append({'name':name,'start_ns':start,'end_ns':end,'status':'ok','result':getattr(result,'name',result)})
            return result
        return call

def scorer(game):
    proxy=TimedProxy(game)
    try:
        result=_coherent_progress_sample(proxy,vd.GameVariable,10.0).as_dict()
        status='returned'; error=None
    except BaseException as exc:
        result=None; status='raised'; error={'type':type(exc).__name__,'message':str(exc)}
    return {'status':status,'result':result,'error':error,'getters':proxy.events}

def main():
    if hashlib.sha256(WAD.read_bytes()).hexdigest()!=EXPECTED_WAD or not SCORER.is_file():
        raise SystemExit('STOP_SETUP_OR_INFRA: fixture/scorer identity mismatch')
    rows=[]
    for i in range(3):
        game=vd.DoomGame()
        row={'schema':'issue3453-construction-clock46-v1','index':i,'mode_requested':str(vd.Mode.ASYNC_SPECTATOR),'ticrate_requested':35,'wad_sha256':hashlib.sha256(WAD.read_bytes()).hexdigest(),'scorer_sha256':hashlib.sha256(SCORER.read_bytes()).hexdigest(),'setup_status':'not_started','cleanup':{'game_closed':False}}
        try:
            game.set_doom_game_path(str(WAD)); game.set_doom_map('map01'); game.set_window_visible(False); game.set_sound_enabled(False)
            game.set_mode(vd.Mode.ASYNC_SPECTATOR); game.set_ticrate(35); game.set_available_buttons([]); game.set_episode_timeout(350); game.set_seed(345600+i)
            game.init(); game.new_episode(); row['setup_status']='ok'; row['mode_readback']=str(game.get_mode()); row['ticrate_readback']=int(game.get_ticrate())
            row['passive_start_ns']=time.monotonic_ns(); row['passive_reads']=[]
            deadline=time.monotonic()+1.5
            while time.monotonic()<deadline:
                a=time.monotonic_ns(); tic=int(game.get_episode_time()); b=time.monotonic_ns()
                row['passive_reads'].append({'start_ns':a,'end_ns':b,'tic':tic})
                time.sleep(.01)
            row['passive_end_ns']=time.monotonic_ns(); row['api_tic_before_action']=int(game.get_episode_time())
            row['scorer_before_action']=scorer(game)
            row['advance_action_start_ns']=time.monotonic_ns()
            try:
                game.advance_action(1)
                row['advance_action_status']='returned'
            except BaseException as exc:
                row['advance_action_status']='raised'; row['advance_action_error']={'type':type(exc).__name__,'message':str(exc)}
            row['advance_action_end_ns']=time.monotonic_ns(); row['api_tic_after_action']=int(game.get_episode_time())
            row['scorer_after_action']=scorer(game)
        except BaseException as exc:
            row['setup_status']='STOP_SETUP_OR_INFRA'; row['setup_error']={'type':type(exc).__name__,'message':str(exc)}
        finally:
            try: game.close(); row['cleanup']['game_closed']=True
            except BaseException as exc: row['cleanup_error']={'type':type(exc).__name__,'message':str(exc)}
            trace=Path('/tmp/vizdoom-tic-entry-v2.bin')
            if trace.is_file():
                data=trace.read_bytes(); import struct
                row['tic_entry_records']=[list(struct.unpack_from('<QQii',data,j)) for j in range(0,len(data)-23,24)]
                row['trace_sha256']=hashlib.sha256(data).hexdigest()
            row['exit_ns']=time.monotonic_ns(); rows.append(row)
            with OUT.open('a',encoding='utf-8') as f: f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
    print(json.dumps({'rows':len(rows),'setup_ok':sum(r['setup_status']=='ok' for r in rows),'closed':sum(r['cleanup']['game_closed'] for r in rows),'advance_returned':sum(r.get('advance_action_status')=='returned' for r in rows)},sort_keys=True))

if __name__=='__main__': main()
