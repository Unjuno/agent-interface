"""Fake X bootstrap only; actual standard MCP main owns the stdio server."""
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from runtime.cli_v1.mcp_server import main
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.test_observation_worker import reader_backend


def main_bootstrap():
    directory = Path(sys.argv[1]).resolve()
    arm,condition = sys.argv[2:4]
    case = unittest.TestCase()
    fake = FakeX(case)
    fake.backend.d.get_display_name = lambda:':fake-qualified'
    start = 1_000_000
    def clock(): return start+5_000_000_000 if (directory/'expire.flag').exists() else start
    def state():
        value = dict(pid=os.getpid(),fake_keys_down=sorted(fake.down),emissions=fake.emissions)
        temporary = directory/'state.tmp'
        temporary.write_text(json.dumps(value),encoding='utf-8')
        temporary.replace(directory/'state.json')
    original_emit = fake.emit
    def emit(*args): original_emit(*args);state()
    def gate():
        if condition=='healthy' or 1 not in fake.down: return
        marker = directory/'gate.tmp'
        marker.write_text(json.dumps(dict(pid=os.getpid(),
            original_deadline_ns=fake.backend.owner.deadline,fake_keys_down=sorted(fake.down))),encoding='utf-8')
        marker.replace(directory/'gate.json')
        until = time.monotonic()+10
        while not (directory/'release.flag').exists():
            if time.monotonic()>=until: raise TimeoutError('harness gate not released')
            time.sleep(.005)
    capture = fake.backend.observe_read_only
    def gated_capture(*args,**kwargs): gate();return capture(*args,**kwargs)
    fake.backend.observe_read_only = gated_capture
    def image(*args): gate();return SimpleNamespace(data=fake.raw,depth=24,visual=1)
    backend = reader_backend(fake,image)
    backend.d.close = lambda:(directory/'observation-reader-closed.json').write_text('{}',encoding='utf-8')
    original_keyboard = NativeHandleBridge.keyboard
    def keyboard(bridge,alias,offset,*,tail,expires_at_ns=None):
        with bridge.input_guard(alias,offset,tail=tail,verify=lambda *args:True):
            return original_keyboard(bridge,alias,offset,tail=tail,expires_at_ns=expires_at_ns)
    argv = ['mcp','--targets',str(directory/'targets.json'),
        '--output-directory',str(directory/'runtime'),'--session-mode','guarded-x11',
        '--guarded-process-identity','--guarded-query-worker']
    if arm=='isolated': argv.append('--guarded-observation-worker')
    state()
    with patch('sys.argv',argv),patch('time.monotonic_ns',side_effect=clock), \
            patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit), \
            patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend',return_value=backend), \
            patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity',side_effect=lambda *args:fake.generation), \
            patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries') as query, \
            patch.object(NativeHandleBridge,'keyboard',keyboard), \
            patch('Xlib.display.Display',side_effect=AssertionError('real display forbidden')):
        query.return_value.read.side_effect = lambda op,xid:True if op=='focus' else fake.generation
        try: main()
        finally: case.doCleanups()


if __name__=='__main__': main_bootstrap()
