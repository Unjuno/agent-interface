import hashlib, json, os, pathlib, time
from vizdoom import DoomGame, GameVariable, Mode

out = pathlib.Path('/out')
game = DoomGame()
game.load_config('/usr/local/lib/python3.12/site-packages/vizdoom/scenarios/doom2.cfg')
game.set_window_visible(False)
variables = [GameVariable.HEALTH, GameVariable.SELECTED_WEAPON, GameVariable.SELECTED_WEAPON_AMMO] + [getattr(GameVariable, f'AMMO{i}') for i in range(10)]
for variable in variables:
    game.add_available_game_variable(variable)
game.init()
game.new_episode()
rows=[]
for phase, ticks in [('initial', 0), ('coast', 35)]:
    if ticks:
        before=int(game.get_episode_time())
        game.advance_action(ticks, True)
        after=int(game.get_episode_time())
    else:
        before=after=int(game.get_episode_time())
    state=game.get_state()
    image=state.screen_buffer
    from PIL import Image
    png=out/f'{phase}.png'
    Image.fromarray(image.transpose(1,2,0)).save(png)
    direct={v.name: game.get_game_variable(v) for v in variables}
    state_values={v.name: float(state.game_variables[i]) for i,v in enumerate(variables)}
    rows.append({'phase':phase,'tic_before':before,'tic_after':after,'state_tic':state.number,'direct':direct,'state_game_variables':state_values,'png':png.name,'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
(out/'raw.json').write_text(json.dumps({'schema':'selected-ammo-signal-a01-v1','run_id':'59-selected-ammo-semantics-a01-20261004','inputs_submitted':[],'game_variable_order':[v.name for v in variables],'rows':rows},indent=2))
game.close()
print(json.dumps({'run_id':'59-selected-ammo-semantics-a01-20261004','rows':rows},indent=2))
