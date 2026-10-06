"""Separate stdlib-only reader of retained native construction artifacts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


def require(value, label):
    if not value:
        raise ValueError(label)


root, dest = map(Path, sys.argv[1:])
start = datetime.now(timezone.utc).isoformat()
first = json.loads((root / 'private/native01/receipt.json').read_text())
second = json.loads((root / 'private/native02/receipt.json').read_text())
require(first['client_exit'] == first['state_after']['ExitCode'] == 139,
        'first native constructor attempt must retain139')
require(second['client_exit'] == second['state_after']['ExitCode'] == 2,
        'repaired native control must retain STOP2')
for receipt in [first, second]:
    require(receipt['state_after']['Running'] is False, 'container not terminal')
    require(receipt['state_after']['OOMKilled'] is False, 'OOM qualification')
    require(receipt['source_before'] == receipt['source_after'], 'execution source changed')
require(first['source_before'] == second['source_before'], 'game/controller source differs')
require(not (root/'native01/control/ROW.json').exists(), 'first missing row rewritten')
for p in ['native01/attack', 'native02/attack']:
    require(not (root/p).exists(), 'attack must remain NOT_RUN')
row_path = root / 'native02/control/ROW.json'
row = json.loads(row_path.read_text())
require('error' not in row, 'second row has a setup exception')
samples = row['privileged_samples']
require(len(samples) == 7, 'expected7 saved getter snapshots')
require(all(type(s['episode_tic']) is int and s['episode_tic'] == 14
            and type(s['episode_tic_after']) is int and s['episode_tic_after'] == 14
            and type(s['ammo']) is int and s['ammo'] == 50
            and type(s['kills']) is int and s['kills'] == 0
            and s['dead'] is False for s in samples), 'getter-table mismatch')
require(samples[-1]['begin_ns'] - samples[0]['begin_ns'] >= 1_000_000_000,
        'saved getter interval shorter than1s')
keys = [e for e in row['events'] if e.get('event') == 'independent_X11_keymap']
require(len(keys) == 2, 'neutral queries absent')
for event in keys:
    require(len(event['bitmap']) == 32 and all(type(b) is int and b == 0
            for b in event['bitmap']), 'private server keymap not neutral')
    require(event['space_down'] is False, 'space must remain up in control')
require(not any(e.get('event') == 'input_admission' for e in row['events']),
        'control admits input')
require(len(row['cleanup']) == 4, 'missing cleanup resource')
require(all(e.get('closed') is True for e in row['cleanup'][:3]), 'close did not return')
require(row['cleanup'][0]['thread_alive_after_close'] is False, 'owner thread remains')
require(row['cleanup'][3]['resource'] == 'Xvfb' and
        row['cleanup'][3]['returncode'] == 0, 'Xvfb not reaped0')
pngs = {name: hashlib.sha256((root/'native02/control'/name).read_bytes()).hexdigest()
        for name in ['before.png', 'after.png']}
require(pngs['before.png'] != pngs['after.png'], 'retained encoded PNGs unexpectedly identical')
runtime = json.loads((root/'native02/RUNTIME.json').read_text())
require(runtime['limits'] == {'cpu.max':'100000 100000',
        'memory.max':'805306368', 'pids.max':'96'}, 'observed cgroup config differs')
result = {'utc_start':start, 'utc_end':datetime.now(timezone.utc).isoformat(),
          'disposition':'STOP_NO_ADVANCING_GETTER_CLOCK',
          'first_native_exit':139, 'repaired_control_exit':2,
          'attack':'NOT_RUN', 'row_sha256':hashlib.sha256(row_path.read_bytes()).hexdigest(),
          'getter_tics':[s['episode_tic'] for s in samples],
          'getter_ammo':[s['ammo'] for s in samples], 'png_sha256':pngs,
          'getter_bracket_ns':samples[-1]['begin_ns']-samples[0]['begin_ns'],
          'neutral_X11_queries':2, 'no_admission_in_control':True,
          'source_unchanged_between_attempts':True,
          'limits_are_observed_configuration_not_adversarial_enforcement':True,
          'no_game_input_effect_release_useful_feedback_PASS':True,
          'first_game_stack_location_and_live_tick_truth':'UNKNOWN'}
with dest.open('x') as f:
    json.dump(result,f,sort_keys=True,indent=2)
    f.write('\n')
print(json.dumps(result,sort_keys=True))
