"""Explicit Inkscape cause-delivery episode; injected interruption, manual stages."""
import argparse
import contextlib
import io
import json
import threading
import time
import uuid
from pathlib import Path
from Xlib import X, XK, display
from pointer_exchange_v1 import run
from decision_receipt_v2 import build
from receipt_image import select_image
from report_pages_v2 import digest
from unix_json_deadline import exchange

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['initial', 'interrupt', 'recover', 'finish'])
    ap.add_argument('socket')
    ap.add_argument('root', type=Path)
    args = ap.parse_args()
    root, runtime = args.root, args.root / 'runtime'
    out = root / args.stage
    out.mkdir(exist_ok=False)
    def save(name, value):
        (out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    def read(path):
        return json.loads((root / path).read_text())
    def query(q):
        return exchange(args.socket, q, timeout=16)
    if args.stage == 'initial':
        names = ['cause_live_v1.py', 'cause_interactive_v1.py', 'cause_session_v1.py',
                 'cause_socket_entry_v1.py', 'input_owner_v10.py', 'executor_v4.py',
                 'lease_cause_v1.py', 'pointer_exchange_v1.py', 'decision_receipt_v1.py',
                 'decision_receipt_v2.py', 'event_socket_v11.py', 'receipt_image.py']
        save('plan', {'sources': {n: digest((HERE / n).read_bytes()) for n in names},
                     'allocation': 'one fresh Inkscape seed 207; retain failed stages; explicit recovery only',
                     'scope': 'candidate integration and model review; injected fault, no speed comparison',
                     'verified_model_id': None, 'model_tokens': None})
        batch = query({'after': 0, 'events': ['observation'], 'timeout': 5})
        save('batch', batch)
        result = {'batch': batch, 'image': select_image(batch, runtime)}
    elif args.stage in ('interrupt', 'recover'):
        prior = read('initial/batch.json') if args.stage == 'interrupt' else read('interrupt/report.json')['last_reply']
        steps = ([{'op': 'hold', 'keys': ['Control_L'], 'duration_ms': 1000},
                  {'op': 'hold', 'keys': ['Right'], 'duration_ms': 80}]
                 if args.stage == 'interrupt' else
                 [{'op': 'pointer_click', 'x': 618, 'y': 391, 'duration_ms': 80},
                  {'op': 'hold', 'keys': ['Right'], 'duration_ms': 80},
                  {'op': 'chord', 'modifier': 'Control_L', 'key': 's'},
                  {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}])
        save('source-batch', prior)
        save('steps', steps)
        injection = {}
        worker = None
        if args.stage == 'interrupt':
            # A separate X connection controls only this private fixture.
            with contextlib.redirect_stdout(io.StringIO()):
                d = display.Display(read('runtime/fixture.json')['display'])
            def inject():
                original = sink = None
                try:
                    code = d.keysym_to_keycode(XK.string_to_keysym('Control_L'))
                    def down():
                        return bool(d.query_keymap()[code // 8] & (1 << (code % 8)))
                    deadline = time.monotonic() + 10
                    while not down() and time.monotonic() < deadline:
                        time.sleep(.002)
                    assert down(), 'held Control_L not observed'
                    injection['physical_down_before_transfer'] = True
                    original = d.get_input_focus().focus
                    sink = d.screen().root.create_window(0, 0, 100, 80, 0,
                            d.screen().root_depth, override_redirect=True)
                    sink.map()
                    sink.set_input_focus(X.RevertToParent, X.CurrentTime)
                    d.sync()
                    injection['transfer_ns'] = time.perf_counter_ns()
                    deadline = time.monotonic() + 1
                    while down() and time.monotonic() < deadline:
                        time.sleep(.002)
                    injection['physical_up_after_transfer'] = not down()
                    assert injection['physical_up_after_transfer']
                    original.set_input_focus(X.RevertToParent, X.CurrentTime)
                    d.sync()
                    injection['restored_ns'] = time.perf_counter_ns()
                except Exception as exc:
                    injection['error'] = repr(exc)
                finally:
                    if original is not None:
                        original.set_input_focus(X.RevertToParent, X.CurrentTime)
                        d.sync()
                    if sink is not None:
                        sink.destroy()
                        d.sync()
                    d.close()
            worker = threading.Thread(target=inject)
            worker.start()
        report = run(query, prior, runtime, args.stage, steps, 30000, save)
        if worker is not None:
            worker.join()
            save('injection', injection)
        save('report', report)
        receipt = build((out / 'report.json').read_bytes())
        save('receipt', receipt)
        result = {'receipt': receipt, 'image': report.get('image'), 'injection': injection}
    else:
        batch = read('recover/report.json')['last_reply']
        q = {'after': batch['cursor'], 'events': ['independent_evaluation'], 'timeout': 5,
             'request_id': uuid.uuid4().hex, 'command': {'op': 'finish'}}
        save('request', q)
        result = query(q)
    save('result', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
