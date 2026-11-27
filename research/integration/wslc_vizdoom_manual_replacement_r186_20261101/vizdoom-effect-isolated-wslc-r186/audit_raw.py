"""Offline cross-check of r186 recorded positions, events and source hashes."""
import hashlib
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parent
source = root.parent / 'vizdoom-current-owned-target-wslc-r185'
data = json.loads((root / 'output/result.json').read_text())
manifest = json.loads((source / 'source-manifest.json').read_text())

def require(condition, description):
    if not condition:
        raise ValueError(description)

raw_manifest = json.loads((root / 'raw-sha256.json').read_text())
raw_paths = {p.relative_to(root).as_posix() for p in (root / 'output').rglob('*') if p.is_file()}
require(set(raw_manifest) == raw_paths, 'raw inventory mismatch')
for path, expected in raw_manifest.items():
    require(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected,
            'raw hash mismatch: ' + path)
for path, expected in manifest.items():
    require(hashlib.sha256((source / path).read_bytes()).hexdigest() == expected,
            'source hash mismatch: ' + path)
runner = hashlib.sha256((root / 'runner.py').read_bytes()).hexdigest()
require(runner == '254811d7031c1d0b0004d5f98b6bdd5f43f8cadac9f51ae0b7c24ed7ed60c8c3',
        'runner mismatch')
log = [json.loads(line) for line in
       (root / 'output/old-mcp/xvfb-delayed-injections.jsonl').read_text().splitlines() if line]
require(len(log) == 1, 'injection count')
marker = data['old_marker']
require(log[0]['owner_pid'] == marker['owner_pid'] and
        log[0]['delayed_keycode'] == marker['delayed_keycode'] and
        log[0]['flushed_ns'] <= marker['flushed_ns'] and
        marker['flushed_ns'] == data['times']['old_queued'], 'injection marker mismatch')

times = data['times']
horizon = times['old_queued'] + 8_000_000_000
require(times['old_exit'] < times['fresh_started'] < times['recorder_ready'] <
        horizon < times['horizon_end'], 'generation/horizon ordering')
require(times['fresh_game_ready'] < horizon and times['action_started'] < times['horizon_end'],
        'fresh action ordering')
events = data['events']
w, b = marker['immediate_keycode'], marker['delayed_keycode']
for event_type in (2, 3):
    require(any(e['type'] == event_type and e['detail'] == w and
                times['action_started'] <= e['ns'] < times['horizon_end'] for e in events),
            'fresh W event missing')
require(not any(e['type'] == 2 and e['detail'] == b and e['ns'] < times['horizon_end']
                for e in events), 'B observed before horizon')
require(any(e['type'] == 2 and e['detail'] == b and e['ns'] >= times['horizon_end']
            for e in events), 'B positive control missing')
coast = math.dist(data['coast_before'], data['coast_after'])
move = math.dist(data['coast_after'], data['move_after'])
require(abs(coast - data['coast_displacement']) < 1e-9 and coast < 1, 'coast mismatch')
require(abs(move - data['move_displacement']) < 1e-9 and move > 5, 'move mismatch')
require(data['old_target_exit_before_display_kill'] is not None and
        data['old_terminal']['cleanup_status'] == 'UNKNOWN' and
        data['old_terminal']['replay_allowed'] is False, 'old target or receipt')
require(data['old_error'] == 'ConnectionClosedError' and
        data['old_auth_error'] == 'DisplayConnectionError', 'old connection/cookie')
require(data['action']['status'] == 'completed' and
        data['action']['result']['status'] == 'completed' and
        data['fresh_close']['verified'] is True, 'fresh action or close')
require(data['status'] == 'PASS' and len(data['checks']) == 18 and
        all(value is True for value in data['checks'].values()), 'runner gates')
require((root / 'r186-exit.txt').read_text().strip() == '0', 'launcher exit')
print(f'PASS: source, marker, event ordering and effect; coast={coast:.3f}, move={move:.3f}')
print('LIMIT: ordering relies on retained runner timestamps; game positions are runtime observations.')
