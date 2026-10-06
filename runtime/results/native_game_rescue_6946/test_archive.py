"""Read immutable native construction evidence; never launch a game."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = '9e2ecdd3970aaf6fc88af9a7ed8e457ffac20ffd'
PACKET = 'research/doom/native_game_readiness_59_20261003_b64b'
BASE = ROOT / PACKET


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads((BASE / path).read_bytes())


class Archive(unittest.TestCase):
    def test_custody_and_source_pins(self):
        files = git('ls-tree', '-r', '--name-only', SOURCE, '--', PACKET).decode().splitlines()
        self.assertEqual(len(files), 79)
        for path in files:
            self.assertEqual((ROOT / path).read_bytes(), git('show', f'{SOURCE}:{path}'))
        manifest = read('PUBLIC_MANIFEST.json')
        self.assertEqual(len(manifest), 78)
        for path, expected in manifest.items():
            data = (BASE / path).read_bytes()
            self.assertEqual({'bytes': len(data), 'sha256': digest(data)}, expected)
        for item in read('PUBLICATION.json'):
            self.assertEqual(digest((BASE / item['public_path']).read_bytes()), item['public_sha256'])
        sources = read('source-pins.json')
        self.assertEqual(len(sources), 4)
        for item in sources:
            data = git('show', f"{item['source_commit']}:{item['repo_path']}")
            self.assertEqual(len(data), item['bytes'])
            self.assertEqual(digest(data), item['sha256'])
            self.assertEqual(data, (BASE / 'native' / item['copy']).read_bytes())

    def test_retained_stop_not_input_success(self):
        first = read('receipts/native01/receipt.json')
        second = read('receipts/native02/receipt.json')
        self.assertEqual(first['client_exit'], 139)
        self.assertEqual(second['client_exit'], 2)
        for attempt, receipt in [('native01', first), ('native02', second)]:
            state = receipt['state_after']
            self.assertEqual(state['ExitCode'], receipt['client_exit'])
            self.assertIs(state['Running'], False)
            self.assertIs(state['OOMKilled'], False)
            self.assertEqual(receipt['source_before'], receipt['source_after'])
            freeze = read('CONSTRUCTION_PINS02.json' if attempt == 'native02' else 'CONSTRUCTION_PINS.json')
            self.assertLessEqual(datetime.fromisoformat(freeze['fixed_before_native_game_start']),
                                 datetime.fromisoformat(receipt['commands'][0]['utc_start']))
            for filename, expected in freeze['source_sha256'].items():
                self.assertEqual(digest((BASE / 'native' / filename).read_bytes()), expected)
        self.assertEqual(first['source_before'], second['source_before'])
        command = next(c['argv'] for c in second['commands'] if '--workdir' in c['argv'])
        self.assertEqual(command[command.index('--workdir') + 1], '/tmp')
        self.assertFalse((BASE / 'native01/control/ROW.json').exists())
        for attempt in ['native01', 'native02']:
            self.assertFalse((BASE / attempt / 'attack').exists())
        row = read('native02/control/ROW.json')
        saved = read('RETAINED_READING.json')
        self.assertEqual(saved['disposition'], 'STOP_NO_ADVANCING_GETTER_CLOCK')
        self.assertEqual(saved['attack'], 'NOT_RUN')
        self.assertEqual(digest((BASE / 'native02/control/ROW.json').read_bytes()), saved['row_sha256'])
        samples = row['privileged_samples']
        self.assertEqual(len(samples), 7)
        for sample in samples:
            for key, value in [('episode_tic', 14), ('episode_tic_after', 14), ('ammo', 50), ('kills', 0)]:
                self.assertIs(type(sample[key]), int)
                self.assertEqual(sample[key], value)
            self.assertIs(sample['dead'], False)
        self.assertEqual(samples[-1]['begin_ns'] - samples[0]['begin_ns'], 1006493992)
        keymaps = [event for event in row['events'] if event.get('event') == 'independent_X11_keymap']
        self.assertEqual(len(keymaps), 2)
        for event in keymaps:
            self.assertEqual(event['bitmap'], [0] * 32)
            self.assertTrue(all(type(x) is int for x in event['bitmap']))
            self.assertIs(event['space_down'], False)
        self.assertFalse(any(e.get('event') == 'input_admission' for e in row['events']))
        self.assertEqual(len(row['cleanup']), 4)
        self.assertTrue(all(e.get('closed') is True for e in row['cleanup'][:3]))
        self.assertIs(row['cleanup'][0]['thread_alive_after_close'], False)
        self.assertEqual(row['cleanup'][3]['returncode'], 0)
        for filename, expected in saved['png_sha256'].items():
            data = (BASE / 'native02/control' / filename).read_bytes()
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(digest(data), expected)
        self.assertNotEqual(saved['png_sha256']['before.png'], saved['png_sha256']['after.png'])


if __name__ == '__main__':
    unittest.main()
