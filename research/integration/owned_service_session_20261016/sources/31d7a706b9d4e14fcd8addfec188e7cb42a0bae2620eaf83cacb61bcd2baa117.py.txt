"""Explicit negative composition: RPC v2 is not a selected-owner adapter.

Fake X only. The metadata shim below exposes owner_id for the current backend;
it deliberately supplies no cancellation relay and is never a production path.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'doom'),str(HERE.parents[1])]
from test_map01_process_identity_backend import backend_fixture,Executor
from test_input_owner_process_v3 import fake_owner,edges
from input_owner_process_v3 import launch_owner_service
from input_owner_rpc_v2 import OwnerRpcClient

ROWS=[]


class ExecutorBoundaryTests(unittest.TestCase):
    def exercise(self,remote,pause):
        case=('remote' if remote else 'local')+('-paused-cancel' if pause else '-normal')
        with tempfile.TemporaryDirectory() as temp, backend_fixture() as (backend,events,_,fake):
            service=client=executor=None;resume=threading.Event();entered=threading.Event()
            row=dict(case=case,metadata_shim_only=remote)
            try:
                if remote:
                    service=launch_owner_service(display=':fake',out=Path(temp)/'service',_owner_factory=fake_owner)
                    client=OwnerRpcClient(service.take_socket(),display=':fake',service_id=service.service_id)
                    # Expose only the missing provenance attribute, to reach the
                    # actual execution boundary. No adapter behavior is invented.
                    client.owner_id=service.startup['owner_id']
                    backend.owner.close();backend.owner=client
                backend.snapshot('source',0)
                original=backend.raw
                def raw(key,down):
                    result=original(key,down)
                    if pause and down:
                        entered.set()
                        if not resume.wait(4):raise RuntimeError('test worker pause deadline')
                    return result
                backend.raw=raw
                executor=Executor(backend,events.append)
                executor.submit(case,[{'op':'hold','keys':['a'],'duration_ms':5}],backend.sequence,
                                time.perf_counter_ns()+10_000_000_000)
                worker=executor.active[2] if executor.active else None
                if pause:
                    self.assertTrue(entered.wait(2))
                    cancelled_at=time.perf_counter_ns()
                    self.assertTrue(executor.cancel(case))
                    # Fixed diagnostic window, not a physical release-time bound.
                    deadline=time.monotonic()+.25
                    while time.monotonic()<deadline:time.sleep(.005)
                    observed=edges(service.out) if remote else None
                    row['paused']=dict(cancelled_at_ns=cancelled_at,observed_at_ns=time.perf_counter_ns(),
                        worker_alive=worker.is_alive(),resume_set=resume.is_set(),
                        parent_cancel=backend.lease.cancel.is_set(),
                        parent_interruption=backend.lease.interruption_snapshot(),
                        edges=observed,local_down=sorted(fake.down) if not remote else None,
                        events=json.loads(json.dumps(events)))
                    self.assertTrue(worker.is_alive());self.assertFalse(resume.is_set())
                    if remote:
                        self.assertEqual([e['event'] for e in observed],[2])
                        self.assertIsNone(backend.lease.interruption_snapshot())
                        self.assertFalse(any(e.get('event')=='input_released' for e in events))
                    else:
                        self.assertEqual(fake.down,set())
                        self.assertIsNotNone(backend.lease.interruption_snapshot())
                    resume.set()
                if worker:worker.join(4)
                self.assertFalse(worker and worker.is_alive())
                terminal=[e for e in events if e.get('event')=='terminal'][-1]
                self.assertEqual(terminal['status'],'cancelled' if pause else 'completed')
                self.assertTrue(terminal['release']['verified'])
                row.update(terminal=terminal,events=events,records=backend.owner.records)
            finally:
                resume.set()
                if executor:executor.close()
                if client:row['client_close']=client.close()
                if service:
                    service.close_channel();row['service_report']=service.wait(6)
                    row.update(startup=service.startup,spawn_pid=service.process.pid,
                               files=service.saved_files(),edges=edges(service.out))
                    self.assertFalse(service.process.is_alive(),'owned service unresolved')
                ROWS.append(row)
            if remote:
                self.assertTrue(row['service_report']['verified'])
                self.assertEqual([e['event'] for e in row['edges']],[2,3])

    def test_local_owner_cancel_releases_while_worker_paused(self):self.exercise(False,True)
    def test_rpc_metadata_shim_cancel_waits_for_worker_to_send_again(self):self.exercise(True,True)
    def test_rpc_metadata_shim_normal_actual_executor_completes(self):self.exercise(True,False)


def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExecutorBoundaryTests))
    root=HERE.parents[1];pins={}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(root) and path.is_file() and path.suffix=='.py':
                pins[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    Path(sys.argv[1]).write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),optimize=sys.flags.optimize,python=sys.version,parent_pid=os.getpid(),
        rows=ROWS,source_sha256_lf=pins),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':main()
