"""One frozen #2907 XID-vs-screen-pixel construction; no app-content input."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from PIL import Image
from Xlib import X, display

from native_handle_bridge_v1 import NativeHandleBridge


ROOT = Path('/out')
DISPLAY = ':95'
CALC_RGB = [216, 34, 34]
INKSCAPE_RGB = [34, 200, 68]
SOURCE_COMMIT = '2dadbde96a3774614f0dff8b51f95dbef9d05716'
IMAGE_ID = 'sha256:44634c6599b9713b382da9937db38d409c9e66bcbce95aaf2bfeae7793c11385'


def main():
    env = dict(os.environ, DISPLAY=DISPLAY)
    os.environ.update(env)
    processes = []
    logs = {}
    bridge = None
    result = {
        'schema': 'issue2907/active-xid-screen-contrast-v1',
        'construction': '03',
        'source_commit': SOURCE_COMMIT,
        'image_id': IMAGE_ID,
        'display': DISPLAY,
        'network': 'none',
        'key_events': 0,
        'pointer_events': 0,
        'model_calls': 0,
        'colors_rgb': {'calc': CALC_RGB, 'inkscape': INKSCAPE_RGB},
        'sample_xy': [400, 300],
    }

    def launch(args, log_name=None):
        stream = None
        if log_name:
            stream = (ROOT / log_name).open('wb')
            logs[log_name] = stream
        process = subprocess.Popen(args, env=env, stdin=subprocess.DEVNULL,
                                   stdout=stream or subprocess.DEVNULL,
                                   stderr=stream or subprocess.DEVNULL)
        processes.append(process)
        return process

    def command(args):
        completed = subprocess.run(args, env=env, text=True, capture_output=True,
                                   timeout=8, check=False)
        if completed.returncode:
            raise RuntimeError(f'{args!r}: exit={completed.returncode}; '
                               f'stderr={completed.stderr[-1000:]}')
        return completed.stdout.strip()

    def window_id(title):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            for row in command(['wmctrl', '-lpG']).splitlines():
                fields = row.split()
                if fields and fields[-1] == title:
                    return int(fields[0], 16)
            time.sleep(0.1)
        raise TimeoutError(f'window not found: {title}')

    def active_id():
        return int(command(['xdotool', 'getactivewindow']))

    def stacking():
        connection = display.Display(DISPLAY)
        prop = connection.screen().root.get_full_property(
            connection.intern_atom('_NET_CLIENT_LIST_STACKING'), X.AnyPropertyType)
        values = [] if prop is None else [int(value) for value in prop.value]
        connection.close()
        return values

    def observation_evidence(observation):
        artifact = observation['native']['artifact']
        path = Path(artifact['path'])
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        with Image.open(path) as opened:
            image = opened.convert('RGB')
            pixel = list(image.getpixel((400, 300)))
            dimensions = list(image.size)
        return {
            'path': str(path),
            'sha256': digest,
            'receipt_sha256': artifact['sha256'],
            'source_raw_sha256': artifact['source_raw_sha256'],
            'native_sha256': observation['native']['sha256'],
            'capture_ns': observation['capture_ns'],
            'dimensions': dimensions,
            'sample_rgb': pixel,
            'sequence': observation['sequence'],
            'binding_revision': observation['binding_revision'],
        }

    try:
        launch(['Xvfb', DISPLAY, '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
               'xvfb.log')
        time.sleep(0.5)
        launch(['openbox', '--sm-disable'], 'openbox.log')
        time.sleep(0.7)
        launch(['xmessage', '-name', 'calc-probe', '-bg', '#d82222', '-fg', '#ffffff',
                '-geometry', '500x400+150+100', 'CALC_SURFACE'])
        time.sleep(0.3)
        launch(['xmessage', '-name', 'inkscape-probe', '-bg', '#22c844', '-fg', '#ffffff',
                '-geometry', '500x400+150+100', 'INKSCAPE_SURFACE'])
        time.sleep(0.5)

        calc = window_id('calc-probe')
        inkscape = window_id('inkscape-probe')
        result.update(calc_xid=calc, inkscape_xid=inkscape,
                      initial_window_list=command(['wmctrl', '-lpG']))

        command(['wmctrl', '-ia', hex(calc)])
        time.sleep(0.2)
        initial_active = active_id()
        initial_stacking = stacking()
        if initial_active != calc or initial_stacking[-1] != calc:
            raise RuntimeError('Calc baseline activation/stacking did not establish')

        bridge = NativeHandleBridge(DISPLAY, {'app': calc}, 'app', ROOT / 'bridge')
        baseline = bridge.observe()
        baseline_evidence = observation_evidence(baseline)

        command(['xdotool', 'windowfocus', str(inkscape)])
        time.sleep(0.2)
        focus_active = active_id()
        focus_stacking = stacking()
        focus_review = bridge.review_window(inkscape)
        focus_observation = focus_review.get('observation')
        focus_evidence = (observation_evidence(focus_observation)
                          if focus_observation else None)

        command(['wmctrl', '-ia', hex(inkscape)])
        time.sleep(0.2)
        activated_active = active_id()
        activated_stacking = stacking()
        activation_review = bridge.review_window(inkscape)
        activation_observation = activation_review.get('observation')
        activation_evidence = (observation_evidence(activation_observation)
                               if activation_observation else None)

        result.update({
            'baseline': {'active_xid': initial_active, 'stacking': initial_stacking,
                         'observation': baseline_evidence},
            'focus_only': {'active_xid': focus_active, 'stacking': focus_stacking,
                           'review': focus_review, 'observation': focus_evidence},
            'ewmh_activation': {'active_xid': activated_active,
                                'stacking': activated_stacking,
                                'review': activation_review,
                                'observation': activation_evidence},
        })
        result['decision'] = 'PASS_FOCUS_PIXEL_SPLIT_WITH_ACTIVATION_CONTROL' \
            if (focus_review.get('status') == 'reviewed'
                and focus_active == inkscape and focus_stacking[-1] == calc
                and focus_evidence and focus_evidence['sample_rgb'] == CALC_RGB
                and activation_review.get('status') == 'reviewed'
                and activated_active == inkscape and activated_stacking[-1] == inkscape
                and activation_evidence
                and activation_evidence['sample_rgb'] == INKSCAPE_RGB) \
            else 'FAIL_OR_NULL_CONTRAST'
    except BaseException as error:
        result.update(decision='STOP_OR_FAIL_EXACT', exception=repr(error),
                      traceback=traceback.format_exc())
    finally:
        if bridge is not None:
            try:
                bridge.close()
            except Exception:
                pass
        cleanup = []
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            cleanup.append({'pid': process.pid, 'returncode': process.poll()})
        for stream in logs.values():
            stream.close()
        result['cleanup'] = cleanup
        (ROOT / 'run.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n',
                                       encoding='utf-8')
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get('decision') != 'STOP_OR_FAIL_EXACT' else 1


if __name__ == '__main__':
    raise SystemExit(main())
