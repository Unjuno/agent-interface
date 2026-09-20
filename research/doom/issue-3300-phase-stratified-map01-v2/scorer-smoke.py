import hashlib
import json
import time
from pathlib import Path

import vizdoom as vd
from session_map01_v13 import _coherent_progress_sample

FIX = Path('/fixture/fixture')
manifest = json.loads((FIX / 'fixture.json').read_text())
save = FIX / manifest['save_file']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert vd.__version__ == manifest['vizdoom']
assert sha(save) == manifest['save_sha256']
assert sha(Path(vd.__file__).parent / 'freedoom2.wad') == manifest['iwad_sha256']

game = vd.DoomGame()
game.set_doom_game_path(str(Path(vd.__file__).parent / 'freedoom2.wad'))
game.set_doom_scenario_path('')
game.set_doom_map(manifest['map'])
game.set_doom_skill(manifest['skill'])
game.set_seed(manifest['seed'])
game.set_mode(vd.Mode.ASYNC_SPECTATOR)
game.set_ticrate(35)
game.set_window_visible(False)
game.set_sound_enabled(False)
game.set_render_hud(False)
game.set_available_game_variables([vd.GameVariable.KILLCOUNT, vd.GameVariable.DEATHCOUNT])

out = Path('/out')
out.mkdir(parents=True, exist_ok=True)
rows = []
try:
    game.init()
    game.load(str(save))
    game.advance_action(1, True)
    for index in range(10):
        start_ns = time.perf_counter_ns()
        tic_before = int(game.get_episode_time())
        try:
            sample = _coherent_progress_sample(game, vd.GameVariable, 600)
            error = None
            payload = sample.as_dict()
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
            payload = None
        tic_after = int(game.get_episode_time())
        end_ns = time.perf_counter_ns()
        rows.append(dict(index=index, tic_before=tic_before, tic_after=tic_after,
                         start_ns=start_ns, end_ns=end_ns, span_ns=end_ns-start_ns,
                         scorer_returned=error is None, error=error, sample=payload))
        time.sleep(0.05)
finally:
    game.close()

with (out / 'scorer_smoke.jsonl').open('w') as stream:
    for row in rows:
        stream.write(json.dumps(row, sort_keys=True) + '\n')
summary = dict(schema='issue-3300-scorer-smoke-v1', formal_allocation=False,
               vizdoom=vd.__version__, mode='ASYNC_SPECTATOR', ticrate_hz=35,
               fixture_manifest_sha256=sha(FIX / 'fixture.json'),
               fixture_save_sha256=sha(save), row_count=len(rows),
               scorer_successes=sum(row['scorer_returned'] for row in rows),
               unique_tics=sorted({row['tic_before'] for row in rows}),
               span_ns=[row['span_ns'] for row in rows],
               limitation='construction smoke only; no phase strata, three-attempt raw trace, or live reliability estimate')
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, sort_keys=True))
