"""Private native-property/pixel fixture. Oracle is scoring-only, not policy input."""
import base64, hashlib, io, json, os, random, select, subprocess, sys, time, uuid
from pathlib import Path
from PIL import Image
from Xlib import X, display
from policy import choose
ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT/'PLAN.json').read_text())
now = time.monotonic_ns

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def enrollment(pipe):
    deadline = time.monotonic() + 5
    data = bytearray()
    while time.monotonic() < deadline:
        if not select.select([pipe], [], [], max(0, deadline-time.monotonic()))[0]: break
        b = os.read(pipe.fileno(), 1)
        if not b: raise RuntimeError('server EOF')
        if b == b'\n': return data.decode()
        data.extend(b)
        if len(data) > 16: raise RuntimeError('server display line oversized')
    raise TimeoutError('server enrollment line deadline')

class Observer:
    def __init__(self, d, epoch):
        self.d, self.epoch, self.calls = d, epoch, []
    def call(self, op, w, function):
        start = now(); value = function()
        self.calls.append({'op': op, 'window': w.id, 'start_ns': start, 'end_ns': now()})
        return value
    def field(self, w, field):
        if field == 'title':
            return self.call('GetProperty:WM_NAME', w, w.get_wm_name)
        tree = self.call('QueryTree', w, w.query_tree)
        if field == 'parent':
            return self.call('GetProperty:parent.WM_NAME', tree.parent, tree.parent.get_wm_name)
        parent_tree = self.call('QueryTree:parent', tree.parent, tree.parent.query_tree)
        others = [s for s in parent_tree.children if s.id != w.id]
        if len(others) != 1: return None
        return self.call('GetProperty:sibling.WM_NAME', others[0], others[0].get_wm_name)
    def image(self, w):
        reply = self.call('GetImage', w, lambda: w.get_image(0, 0, 32, 24, X.ZPixmap, 0xffffffff))
        assert len(reply.data) == 32*24*4, 'unsupported native pixel layout'
        image = Image.frombytes('RGB', (32, 24), reply.data, 'raw', 'BGRX')
        buf = io.BytesIO(); image.save(buf, format='PNG')
        return {'png_base64': base64.b64encode(buf.getvalue()).decode(), 'pixel_sha256': hashlib.sha256(image.tobytes()).hexdigest(), 'native_bytes': len(reply.data)}
    def packet(self, windows, fields, pixels=False):
        start = now(); begin = len(self.calls)
        records = []
        for w in windows:
            record = {'id': w.id, **{f: self.field(w, f) for f in fields}}
            if pixels: record['image'] = self.image(w)
            records.append(record)
        packet = {'epoch': self.epoch, 'records': records}
        return {'packet': packet, 'canonical_bytes': len(encoded(packet)), 'elapsed_ns': now()-start, 'calls': self.calls[begin:]}

def fixture(mode, repeat, out):
    row = {'mode': mode, 'repeat': repeat, 'input_emissions': 0, 'dispatch_authority': False, 'arms': {}, 'cleanup': {}}
    server = d = None; owned = []
    stderr = (out/f'{mode}-{repeat}.stderr').open('xb')
    oracle = None
    try:
        server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0', '160x80x24', '-nolisten', 'tcp', '-noreset'], stdout=subprocess.PIPE, stderr=stderr, bufsize=0)
        row['server_pid'] = server.pid
        name = ':' + enrollment(server.stdout); row['display'] = name
        d = display.Display(name); root = d.screen().root
        row['epoch'] = str(uuid.uuid4())
        row['sequence_started_ns'] = now()
        titles, parents, anchors = ['Save', 'Save'], ['Doc', 'Doc'], ['Ledger', 'Ledger']
        if mode == 'TITLE': titles = ['Target', 'Other']
        elif mode == 'PARENT': parents = ['Target', 'Other']
        elif mode == 'ANCHOR': anchors = ['Target', 'Other']
        elif mode == 'HIDDEN': titles = parents = anchors = [None, None]
        elif mode == 'DUPLICATE': titles = ['Target', 'Target']
        elif mode == 'STALE_HINT': parents = ['Target', 'Other']
        elif mode == 'CONTRADICTORY': titles, parents = ['Target', 'Other'], ['Other', 'Target']
        else: raise ValueError(mode)
        targets = []
        for i in range(2):
            pane = root.create_window(i*80, 0, 72, 72, 0, d.screen().root_depth, X.InputOutput, X.CopyFromParent, background_pixel=0x202020, override_redirect=True)
            child = pane.create_window(12, 12, 32, 24, 0, d.screen().root_depth, X.InputOutput, X.CopyFromParent, background_pixel=0xeeeeee)
            anchor = pane.create_window(12, 48, 32, 8, 0, d.screen().root_depth, X.InputOutput, X.CopyFromParent, background_pixel=0x444444)
            owned += [pane, child, anchor]
            initial_title = ['Target', 'Other'][i] if mode in ('STALE_HINT', 'CONTRADICTORY') else titles[i]
            initial_parent = 'Doc' if mode in ('STALE_HINT', 'CONTRADICTORY') else parents[i]
            for w, title in ((pane, initial_parent), (child, initial_title), (anchor, anchors[i])):
                if title is not None: w.set_wm_name(title)
                w.map()
            gc = child.create_gc(foreground=0x222222)
            child.fill_rectangle(gc, 4, 4, 8, 16); child.fill_rectangle(gc, 20, 4, 8, 16); gc.free()
            targets.append(child)
        d.sync()
        order = [0, 1]; random.Random(PLAN['seed']+repeat).shuffle(order)
        windows = [targets[i] for i in order]
        oracle = {'mode': mode, 'repeat': repeat, 'epoch': row['epoch'], 'intended_id': targets[1 if mode == 'CONTRADICTORY' else 0].id, 'admissible_resolution': mode in ('TITLE', 'PARENT', 'ANCHOR', 'STALE_HINT'), 'source_role_ids': [w.id for w in targets], 'source_cue_values': {'title': titles, 'parent': parents, 'anchor': anchors}}
        observer = Observer(d, row['epoch'])
        row['acquisition'] = observer.packet(windows, ['title', 'parent', 'anchor'])
        sufficient = [f for f in ('title', 'parent', 'anchor') if choose(row['acquisition']['packet']['records'], [f]) is not None]
        hint = sufficient[0] if sufficient else 'title'
        row['hint'] = {'field': hint, 'learned_requirement_only': True, 'authority': False, 'validity_proven': False, 'initial_unique_fields': sufficient, 'source_epoch': row['epoch']}
        if mode in ('STALE_HINT', 'CONTRADICTORY'):
            row['fixture_mutation_started_ns'] = now()
            for i, w in enumerate(targets):
                w.set_wm_name(titles[i])
                owned[i*3].set_wm_name(parents[i])
            d.sync(); row['fixture_mutation_finished_ns'] = now()
        # No oracle, role ordering or source-render arrays enter choose().
        full = observer.packet(windows, ['title', 'parent', 'anchor'], pixels=True)
        full['selected'] = choose(full['packet']['records'], ['title', 'parent', 'anchor'])
        row['arms']['FULL_REACQUIRE'] = full
        guess = observer.packet(windows, [], pixels=True)
        guess['selected'] = windows[0].id
        row['arms']['SIMILARITY_FIRST'] = guess
        for arm in ('MEMORY_CUE', 'FRESH_CUE'):
            result = observer.packet(windows, [hint])
            result['selected'] = choose(result['packet']['records'], [hint])
            row['arms'][arm] = result
        row['sequence_finished_ns'] = now()
    except Exception as exc:
        row['error'] = repr(exc)
    finally:
        if d is not None:
            row['cleanup']['keymap_empty'] = not any(d.query_keymap())
            row['cleanup']['observed_buttons_1_to_3_neutral'] = not bool(d.screen().root.query_pointer().mask & (X.Button1Mask | X.Button2Mask | X.Button3Mask))
            # Destroy top-level owned panes; children follow their parents.
            for w in owned[::3]: w.destroy()
            d.sync(); d.close(); row['cleanup']['connection_closed'] = True
        if server is not None:
            server.terminate(); row['cleanup']['server_exit'] = server.wait(timeout=3)
        stderr.close()
    return row, oracle

def main():
    out = Path(sys.argv[1]); preflight = '--preflight' in sys.argv
    (out/'ENV.json').write_text(json.dumps({'python': sys.version, 'preflight_excluded': preflight, 'cgroups': {p: Path('/sys/fs/cgroup', p).read_text().strip() for p in ('cpu.max', 'memory.max', 'memory.swap.max', 'pids.max')}}, indent=2)+'\n')
    with (out/'raw.jsonl').open('x') as raw, (out/'oracle.jsonl').open('x') as truth:
        for repeat in range(1 if preflight else PLAN['repeats']):
            for mode in (['TITLE', 'PARENT', 'ANCHOR'] if preflight else PLAN['modes']):
                row, oracle = fixture(mode, repeat, out)
                raw.write(json.dumps(row, sort_keys=True)+'\n'); raw.flush(); os.fsync(raw.fileno())
                truth.write(json.dumps(oracle, sort_keys=True)+'\n'); truth.flush(); os.fsync(truth.fileno())
                print(json.dumps({'mode': mode, 'repeat': repeat, 'error': row.get('error'), 'selected': {k: v['selected'] for k, v in row['arms'].items()}}), flush=True)
                if 'error' in row: raise RuntimeError(row['error'])

if __name__ == '__main__': main()
