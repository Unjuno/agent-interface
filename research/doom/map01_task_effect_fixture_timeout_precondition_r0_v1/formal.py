#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, tempfile
import vizdoom as vd

TASK='MAP01-TASK-EFFECT-FIXTURE-TIMEOUT-PRECONDITION-R0-20260919-001'
FIXTURE_TIC=1366
SAVE_SHA='cc5302aa9cda3960248733caa96da1b53adcc4b6a1a2dcfb80675650c9350401'
IWAD_SHA='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'

def sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def run_case(case, fixture_manifest, iwad):
    f=json.loads(fixture_manifest.read_text())
    save=fixture_manifest.parent/f['save_file']
    if f.get('episode_tic')!=FIXTURE_TIC: raise RuntimeError('fixture_episode_tic')
    if sha(save)!=SAVE_SHA: raise RuntimeError('fixture_save_sha')
    if sha(iwad)!=IWAD_SHA: raise RuntimeError('iwad_sha')
    timeout_tics=int(case['timeout_tics'])
    with tempfile.TemporaryDirectory(prefix='map01-timeout-') as td:
        td=pathlib.Path(td); cfg=td/'doom.ini'; cfg.write_text('[Doom.Bindings]\n',encoding='utf-8')
        load=td/'load.png'; shutil.copy2(save,load)
        g=vd.DoomGame()
        g.set_doom_game_path(str(iwad)); g.set_doom_scenario_path(''); g.set_doom_map('MAP01')
        g.set_doom_config_path(str(cfg)); g.set_mode(vd.Mode.ASYNC_SPECTATOR); g.set_ticrate(35)
        g.set_seed(1888000+timeout_tics); g.set_doom_skill(1); g.set_episode_timeout(timeout_tics)
        g.set_window_visible(False); g.set_sound_enabled(False); g.set_console_enabled(False)
        g.set_available_game_variables([vd.GameVariable.DEATHCOUNT,vd.GameVariable.KILLCOUNT])
        g.init()
        try:
            g.load(str(load))
            observed={
              'episode_tic':int(g.get_episode_time()),
              'episode_finished':bool(g.is_episode_finished()),
              'player_dead':bool(g.is_player_dead()),
              'kill_count':int(g.get_game_variable(vd.GameVariable.KILLCOUNT)),
              'death_count':int(g.get_game_variable(vd.GameVariable.DEATHCOUNT)),
            }
        finally: g.close()
    expected_terminal=timeout_tics < FIXTURE_TIC
    return {**case,'expected_terminal':expected_terminal,**observed,'match':observed['episode_finished']==expected_terminal}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--fixture-manifest',required=True); ap.add_argument('--iwad',required=True); ap.add_argument('--cases',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); fixture=pathlib.Path(a.fixture_manifest); iwad=pathlib.Path(a.iwad); cases=json.loads(pathlib.Path(a.cases).read_text())
    if vd.__version__!='1.3.0': raise SystemExit('vizdoom_version')
    rows=[run_case(c,fixture,iwad) for c in cases]
    mismatch=sum(not r['match'] for r in rows)
    exact={r['case_id']:r['episode_finished'] for r in rows}
    counters_clean=all((not r['player_dead'] and r['kill_count']==0 and r['death_count']==0) for r in rows)
    ticks_exact=all(r['episode_tic']==FIXTURE_TIC for r in rows)
    directed=(exact=={'ticks-1365':True,'ticks-1366':False,'ticks-1367':False,'ticks-1400':False,'seconds-39':True,'seconds-40':False})
    good=(len(rows)==6 and mismatch==0 and counters_clean and ticks_exact and directed)
    out={'task':TASK,'decision':'PASS_MAP01_FIXTURE_TIMEOUT_PRECONDITION_SCOPED' if good else 'FAIL_FIXTURE_TIMEOUT_MODEL','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'fixture_tic':FIXTURE_TIC,'predicate':'timeout_tics < fixture_tic','case_count':len(rows),'candidate_expected_mismatch':mismatch,'ticks_exact':ticks_exact,'counters_clean':counters_clean,'directed_cases_pass':directed,'rows':rows,'task_input_actions':0,'advance_action_calls':0}
    p=pathlib.Path(a.out); p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if good else 2)
if __name__=='__main__':main()
