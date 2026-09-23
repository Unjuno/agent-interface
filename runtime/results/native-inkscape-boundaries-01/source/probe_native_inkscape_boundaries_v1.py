"""Fixed allocation for click/key/save boundaries; no adaptive input retries."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import time
import traceback
import xml.etree.ElementTree as ET

from run_native_six_task_self_use_v1 import PrivateSession, suite
from native_handle_bridge_v1 import NativeHandleBridge


def allocation():
    conditions = list(itertools.product((1, 18), (0, 50), (0, 50)))
    return [dict(block=block, count=count, after_click_ms=click, before_save_ms=save)
            for block in range(2)
            for count, click, save in (conditions if block == 0 else reversed(conditions))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reference-source', type=Path, required=True)
    parser.add_argument('--point', nargs=2, type=int, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    reference = json.loads(args.reference_source.read_text())
    artifact = reference['native']['artifact']
    data = Path(artifact['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != artifact['sha256']:
        raise ValueError('reviewed reference image hash mismatch')
    (out/'reference.png').write_bytes(data)
    (out/'reference-source.json').write_bytes(args.reference_source.read_bytes())
    cases = allocation()
    def save(path, value):
        path.write_text(json.dumps(value, indent=2)+'\n')
    save(out/'allocation.json', {'cases': cases, 'point': args.point,
         'reference_sha256': artifact['sha256'], 'initial_image_must_match_exactly': True,
         'expected_svg_step': 2, 'post_save_ms': 300, 'no_adaptive_retry': True})
    rows = []
    for index, case in enumerate(cases):
        folder = out/f'case-{index:02}'
        folder.mkdir()
        row = dict(index=index, **case)
        session = bridge = output = None
        try:
            session = PrivateSession()
            goal, output, _ = suite.prepare(session, 'inkscape', 991086, '')
            window = int(next(line.split()[0] for line in session.windows().splitlines()
                              if output.name in line), 16)
            bridge = NativeHandleBridge(session.name, {'app': window}, 'app', folder/'bridge')
            source = bridge.observe()
            save(folder/'source.json', source)
            if source['native']['artifact']['sha256'] != artifact['sha256']:
                raise ValueError('fresh initial image differs from reviewed reference; no input')
            offset = bridge.mint('shape', source['sequence'], args.point, region_size=(24,14))
            tail = []
            if case['after_click_ms']:
                tail.append({'op':'wait_update', 'timeout_ms':case['after_click_ms']})
            tail += [{'op':'key_chord', 'keys':['Right']} for _ in range(case['count'])]
            if case['before_save_ms']:
                tail.append({'op':'wait_update', 'timeout_ms':case['before_save_ms']})
            tail += [{'op':'key_chord','keys':['CTRL','s']}, {'op':'wait_update','timeout_ms':300}]
            row['started_ns'] = time.monotonic_ns()
            row['result'] = bridge.click('shape', offset, tail=tail)
            row['returned_ns'] = time.monotonic_ns()
            row['observation'] = bridge.observe()
            # Scoring follows all declared input. Never feeds a retry/repair.
            rect = ET.parse(output).getroot().find('{http://www.w3.org/2000/svg}rect')
            row['actual'] = {key: rect.attrib.get(key) for key in ('x','y','width','height','transform')}
            row['expected_x'] = 50 + 2*case['count']
            row['exact'] = (row['result']['status'] == 'completed'
                and float(row['actual']['x']) == row['expected_x']
                and row['actual']['y'] == '50' and row['actual']['width'] == '40'
                and row['actual']['height'] == '30' and row['actual']['transform'] is None)
        except Exception:
            row['error'] = traceback.format_exc()
            row['exact'] = False
        finally:
            if output is not None and output.exists():
                shutil.copyfile(output, folder/'shape.svg')
            if bridge is not None:
                bridge.close()
            if session is not None:
                session.close()
                row['cleanup'] = [{'pid': p.pid, 'returncode': p.poll()} for p in session.procs]
            rows.append(row)
            save(folder/'result.json', row)
            save(out/'results.json', rows)
        print(json.dumps({k: row.get(k) for k in ('index','block','count','after_click_ms',
              'before_save_ms','actual','exact','error')}), flush=True)


if __name__ == '__main__':
    main()
