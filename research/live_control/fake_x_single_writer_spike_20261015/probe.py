"""Research-only Fake X separation spike; no real display or input."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import queue
import subprocess
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

from Xlib import X
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError

ROOT = Path(__file__).resolve().parents[3]
MATRIX = [('coupled','healthy'), ('separated','healthy'), ('coupled','cancel'),
          ('separated','cancel'), ('coupled','expiry'), ('separated','expiry'),
          ('separated','duplicate_cancel'), ('separated','cleanup_sync_block'),
          ('separated','cleanup_emit_block'), ('separated','unknown_readback')]


class Case:
    def __init__(self, arm, mode):
        self.arm, self.mode = arm, mode
        self.now, self.deadline, self.epoch = 1_000_000, 11_000_000, 0
        self.cancel = threading.Event()
        self.wake = threading.Event()
        self.query_entered, self.query_resume = threading.Event(), threading.Event()
        self.backend_entered, self.backend_resume = threading.Event(), threading.Event()
        self.cleaned = threading.Event()
        self.replies = queue.Queue()
        self.lock = threading.RLock()
        self.events, self.keys, self.buttons, self.errors = [], set(), set(), []
        self.revoked, self.cleaning, self.receipt, self.owner_tid = False, False, None, None
        backend = self.backend = object.__new__(X11Backend)
        backend.held_keycodes, backend.held_buttons, backend.emissions = {}, set(), 0
        backend._keycode = {'CTRL':1, 'a':2}.__getitem__
        backend._before_input_press = self.before_press
        backend.d = SimpleNamespace(sync=self.sync, query_keymap=self.keymap)
        backend.root = SimpleNamespace(query_pointer=self.pointer)

    def event(self, name, **data):
        with self.lock:
            self.events.append(dict(n=len(self.events), event=name, clock_ns=self.now,
                thread_id=threading.get_ident(), **data))

    def require_owner(self):
        if threading.get_ident() != self.owner_tid:
            raise RuntimeError('second input writer forbidden')

    def before_press(self):
        self.require_owner()
        with self.lock:
            if self.revoked or self.cancel.is_set() or self.now >= self.deadline:
                raise X11BackendError('revoked/expired before positive input')

    def wait(self, gate):
        if not gate.wait(5):
            raise TimeoutError('harness boundary did not resume')

    def emit(self, _connection, kind, code):
        self.require_owner()
        if self.cleaning and self.mode == 'cleanup_emit_block':
            self.event('backend_block', boundary='cleanup_emit')
            self.backend_entered.set()
            self.wait(self.backend_resume)
        with self.lock:
            if kind == X.KeyPress: self.keys.add(code)
            elif kind == X.KeyRelease: self.keys.discard(code)
            elif kind == X.ButtonPress: self.buttons.add(code)
            elif kind == X.ButtonRelease: self.buttons.discard(code)
            else: raise RuntimeError('unexpected fake X injection')
            self.event('injected', kind=kind, code=code, cleanup=self.cleaning)

    def sync(self):
        if self.cleaning and self.mode == 'cleanup_sync_block':
            self.event('backend_block', boundary='cleanup_sync')
            self.backend_entered.set()
            self.wait(self.backend_resume)

    def keymap(self):
        if self.cleaning and self.mode == 'unknown_readback':
            self.event('readback_error')
            raise OSError('fake readback unavailable')
        bitmap = bytearray(32)
        with self.lock:
            for code in self.keys:
                bitmap[code//8] |= 1 << (code%8)
            self.event('keymap_read', keys=sorted(self.keys))
        return bitmap

    def pointer(self):
        with self.lock:
            mask = sum({1:X.Button1Mask, 3:X.Button3Mask}[button] for button in self.buttons)
            self.event('pointer_read', buttons=sorted(self.buttons))
        return SimpleNamespace(mask=mask)

    def query(self):
        self.event('query_started')
        self.query_entered.set()
        self.wait(self.query_resume)
        proof = {'epoch':0, 'source_id':'fake-source-0', 'deadline_ns':self.deadline}
        self.event('query_returned', proof=proof)
        return proof

    def query_worker(self):
        try:
            self.replies.put(self.query())
            self.wake.set()
        except BaseException as error:
            self.errors.append(repr(error))

    def cleanup(self):
        self.require_owner()
        if self.cleaned.is_set():
            raise RuntimeError('duplicate cleanup')
        self.cleaning = True
        self.event('cleanup_requested')
        try:
            receipt = self.backend.release_all()
            with self.lock:
                self.receipt = receipt
                self.event('cleanup_returned', receipt=self.receipt)
        except Exception as error:
            with self.lock:
                self.receipt = {'verified':False, 'error':repr(error), 'state':'unknown'}
                self.event('cleanup_unknown', receipt=self.receipt)
        finally:
            self.cleaning = False
            self.cleaned.set()

    def revoke_if_needed(self):
        changed = False
        with self.lock:
            if not self.revoked and (self.cancel.is_set() or self.now >= self.deadline):
                self.revoked = True
                self.epoch += 1
                self.event('authority_revoked', epoch=self.epoch,
                           reason='cancel' if self.cancel.is_set() else 'expiry')
                changed = True
        if changed:
            self.cleanup()

    def owner(self):
        self.owner_tid = threading.get_ident()
        try:
            self.backend.key_state('CTRL', True)
            self.backend.pointer_button('left', True)
            self.event('prefix_held')
            if self.arm == 'coupled':
                proof = self.query()
            else:
                self.observer = threading.Thread(target=self.query_worker, name='fake-observer')
                self.observer.start()
                while True:
                    self.revoke_if_needed()
                    try:
                        proof = self.replies.get_nowait()
                        break
                    except queue.Empty:
                        self.wake.wait(.01)
                        self.wake.clear()
            self.revoke_if_needed()
            if self.revoked or proof['epoch'] != self.epoch or self.now >= proof['deadline_ns']:
                self.event('reply_discarded', proof=proof, current_epoch=self.epoch)
            else:
                self.event('reply_admitted', proof=proof, current_epoch=self.epoch)
                self.backend.key_state('a', True)
                self.backend.pointer_button('right', True)
            if not self.cleaned.is_set():
                self.cleanup()
        except BaseException as error:
            self.errors.append(repr(error))
        finally:
            self.event('owner_returned')

    def snapshot(self, owner):
        with self.lock:
            return dict(keys=sorted(self.keys), buttons=sorted(self.buttons),
                owner_alive=owner.is_alive(), observation_blocked=not self.query_resume.is_set(),
                receipt=self.receipt, revoked=self.revoked, epoch=self.epoch,
                clock_ns=self.now, deadline_ns=self.deadline, event_count=len(self.events))

    def run(self):
        worker = threading.Thread(target=self.owner, name='fake-input-owner')
        with patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=self.emit), \
                patch('Xlib.display.Display', side_effect=RuntimeError('real X forbidden')):
            worker.start()
            try:
                self.wait(self.query_entered)
                if self.mode != 'healthy':
                    if self.mode == 'expiry':
                        with self.lock:
                            self.now = self.deadline
                            self.event('clock_advanced')
                    else:
                        for _ in range(2 if self.mode == 'duplicate_cancel' else 1):
                            with self.lock:
                                self.cancel.set()  # retained state before wake hint
                                self.event('cancel_requested')
                    self.wake.set()
                    if self.arm == 'separated':
                        self.wait(self.backend_entered if self.mode in
                            ('cleanup_emit_block','cleanup_sync_block') else self.cleaned)
                blocked = self.snapshot(worker)
            finally:
                self.backend_resume.set()
                backend_resumed = None
                if self.mode in ('cleanup_emit_block','cleanup_sync_block') and self.backend_entered.is_set():
                    self.wait(self.cleaned)
                    backend_resumed = self.snapshot(worker)
                self.query_resume.set()
                self.wake.set()
                worker.join(5)
                if hasattr(self,'observer'):
                    self.observer.join(5)
            if worker.is_alive() or (hasattr(self,'observer') and self.observer.is_alive()):
                self.errors.append('harness threads did not stop')
        return dict(arm=self.arm, mode=self.mode, boundary=blocked, backend_resumed=backend_resumed,
            final=self.snapshot(worker), events=self.events, errors=self.errors,
            owner_thread_id=self.owner_tid,
            pending_backend_keys=dict(self.backend.held_keycodes),
            pending_backend_buttons=sorted(self.backend.held_buttons))


def write_fresh(path, row):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(row, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    here = Path(__file__).parent
    if args.freeze:
        files = [*sorted(here.glob('*.py')), here/'PLAN.md', here/'.gitattributes', *sorted((ROOT/'runtime').rglob('*.py'))]
        write_fresh(args.freeze, dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            files={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            matrix=MATRIX, source_hash_scope='Exact bytes of materialized checkout files; not all repository sources.',
            python_xlib=importlib.metadata.version('python-xlib'),
            physical_release_bound_claimed=False, live_allocation_invocations=0))
        return
    if args.output is None or args.output.exists():
        parser.error('fresh --output required')
    freeze_path = here/'SOURCE_FREEZE.json'
    frozen = json.loads(freeze_path.read_bytes())
    for name, digest in frozen['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('frozen source changed: '+name)
    cases = []
    current = None
    try:
        for arm, mode in MATRIX:
            current = Case(arm,mode)
            cases.append(current.run())
    except BaseException as error:
        if current is not None:
            cases.append(dict(arm=current.arm,mode=current.mode,partial=True,
                events=current.events,errors=current.errors,keys=sorted(current.keys),
                buttons=sorted(current.buttons),receipt=current.receipt))
        write_fresh(args.output, dict(scope='FAKE_X_SEPARATION_SPIKE', cases=cases,
                    collection_error=repr(error), live_allocation_invocations=0))
        raise
    write_fresh(args.output, dict(scope='FAKE_X_SEPARATION_SPIKE', python=sys.version,
        platform=platform.platform(), optimized=sys.flags.optimize, cases=cases,
        freeze_sha256=hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
        real_x_connection=False, live_allocation_invocations=0))
    print('saved', len(cases), 'Fake X cases')


if __name__ == '__main__':
    main()
