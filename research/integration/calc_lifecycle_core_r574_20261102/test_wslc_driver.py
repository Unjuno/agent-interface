import json, subprocess, tempfile, unittest
from pathlib import Path
from wslc_driver import ContainerDriver

RUN='b'*32
CID='a'*64
IMAGE='sha256:'+'1'*64

class FakeCli:
    def __init__(self, root, responses):self.root=root;self.responses=iter(responses);self.calls=[]
    def __call__(self,args,timeout):
        self.calls.append(args)
        x=next(self.responses)
        if isinstance(x,BaseException):raise x
        if args[1]=='run':(self.root/'container.cid').write_text(CID)
        return subprocess.CompletedProcess(args,x.get('code',0),x.get('out',b''),x.get('err',b''))

def state(*, cid=CID, run=RUN, running=False, code=0):
    return json.dumps([{'Id':cid,'Config':{'Labels':{'agent-interface.run-id':run}},
                        'State':{'Running':running,'Status':'running' if running else 'exited','ExitCode':code}}]).encode()

class DriverTests(unittest.TestCase):
    def test_start_and_wait_record_identity_and_exit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,[{'out':CID.encode(),'err':b'swap warning'}, {'out':state(running=True)}, {'out':state(code=7)}])
            driver=ContainerDriver(root,RUN,IMAGE,['python3','-c','pass'],runner=cli)
            self.assertEqual(driver.start(timeout_s=3)['status'],'running')
            result=driver.wait(timeout_s=3)
            self.assertEqual((result['status'],result['exit_code']),('exited',7))
            self.assertTrue((root/'identity.json').exists())
            self.assertTrue((root/'commands.jsonl').exists())
            self.assertNotIn('--rm',cli.calls[0])
            self.assertIn('--network',cli.calls[0])

    def test_launch_stdout_mismatch_stays_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,[{'out':b'c'*64}])
            driver=ContainerDriver(root,RUN,IMAGE,['x'],runner=cli)
            self.assertEqual(driver.start(timeout_s=3)['status'],'UNKNOWN')
            self.assertEqual(len(cli.calls),1)

    def test_identity_mismatch_is_unknown_and_does_not_signal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,[{'out':CID.encode()}, {'out':state(run='c'*32)}])
            driver=ContainerDriver(root,RUN,IMAGE,['python3','-c','pass'],runner=cli)
            result=driver.start(timeout_s=3)
            self.assertEqual(result['status'],'UNKNOWN')
            self.assertEqual(len(cli.calls),2)
            self.assertFalse(any('stop' in x or 'remove' in x for x in cli.calls))

    def test_failed_launch_retains_identity_without_asserting_absence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,[subprocess.TimeoutExpired('wslc',1,output=b'partial')])
            driver=ContainerDriver(root,RUN,IMAGE,['python3','-c','pass'],runner=cli)
            result=driver.start(timeout_s=3)
            self.assertEqual(result['status'],'UNKNOWN')
            self.assertTrue((root/'identity.json').exists())
            self.assertIn('cGFydGlhbA==', (root/'commands.jsonl').read_text())

    def test_existing_identity_file_prevents_any_launch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'identity.json').write_text('keep');cli=FakeCli(root,[])
            with self.assertRaises(FileExistsError):ContainerDriver(root,RUN,IMAGE,['x'],runner=cli)
            self.assertEqual(cli.calls,[])
            self.assertEqual((root/'identity.json').read_text(),'keep')

    def test_missing_cid_cannot_trigger_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,[subprocess.TimeoutExpired('wslc',1)])
            driver=ContainerDriver(root,RUN,IMAGE,['x'],runner=cli)
            driver.start(timeout_s=3)
            result=driver.reconcile(timeout_s=1)
            self.assertEqual(result['reason'],'cid_unavailable')
            self.assertEqual(len(cli.calls),1)

    def test_readonly_source_mount_and_validated_route_are_encoded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.mkdir();run=root/'run';run.mkdir()
            cli=FakeCli(run,[])
            driver=ContainerDriver(run,RUN,IMAGE,['python3','/in/runner.py'],runner=cli,
                                   mounts={'/src':(source,True)},environment={'ROUTE':'direct'})
            self.assertIn('type=bind,source='+str(source.resolve())+',target=/src,readonly',driver.args)
            self.assertIn('ROUTE=direct',driver.args)
            with self.assertRaises(ValueError):
                ContainerDriver(root,RUN,IMAGE,['x'],mounts={'/src':(source,False)},runner=cli)
            self.assertEqual(cli.calls,[])

    def test_unknown_launch_cannot_be_promoted_by_wait(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,[{'out':b'c'*64}])
            driver=ContainerDriver(root,RUN,IMAGE,['x'],runner=cli)
            self.assertEqual(driver.start(timeout_s=3)['status'],'UNKNOWN')
            self.assertEqual(driver.wait(timeout_s=3)['status'],'UNKNOWN')
            self.assertEqual(len(cli.calls),1)

    def test_partial_launch_can_reconcile_using_same_transport(self):
        row=lambda status:json.dumps({'ID':CID,'State':status}).encode()+b'\n'
        responses=[subprocess.TimeoutExpired('wslc',1),
                   {'out':state(running=True)},{'out':row('running')},
                   {'out':(CID+'\n').encode()},{'out':row('exited')},
                   {'out':state(code=137)},{'out':row('exited')},
                   {'out':(CID+'\n').encode()},{'out':b''}]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,responses)
            driver=ContainerDriver(root,RUN,IMAGE,['x'],runner=cli)
            self.assertEqual(driver.start(timeout_s=3)['status'],'UNKNOWN')
            (root/'container.cid').write_text(CID)
            result=driver.reconcile(timeout_s=5)
            self.assertEqual(result['task_status'],'UNKNOWN')
            self.assertEqual(result['remove']['status'],'observed_absent')
            self.assertEqual(result['remove']['observed_exit_code'],137)
            self.assertEqual(len(cli.calls),9)

    def test_wait_timeout_then_reconcile_never_claims_task_success(self):
        row=lambda status:json.dumps({'ID':CID,'State':status}).encode()+b'\n'
        responses=[{'out':CID.encode()},{'out':state(running=True)},
                   subprocess.TimeoutExpired('wslc',1),
                   {'out':state(running=True)},{'out':row('running')},
                   {'out':(CID+'\n').encode()},{'out':row('exited')},
                   {'out':state(code=137)},{'out':row('exited')},
                   {'out':(CID+'\n').encode()},{'out':b''}]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,responses)
            driver=ContainerDriver(root,RUN,IMAGE,['x'],runner=cli)
            self.assertEqual(driver.start(timeout_s=3)['status'],'running')
            self.assertEqual(driver.wait(timeout_s=3)['status'],'UNKNOWN')
            receipt=driver.reconcile(timeout_s=5)
            self.assertEqual(receipt['task_status'],'UNKNOWN')
            self.assertEqual(receipt['remove']['observed_exit_code'],137)
            self.assertEqual(receipt['remove']['status'],'observed_absent')

    def test_malformed_status_or_exit_is_never_exited(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cli=FakeCli(root,[{'out':CID.encode()},{'out':state(running=True)},{'out':state(code=True)}])
            driver=ContainerDriver(root,RUN,IMAGE,['x'],runner=cli)
            driver.start(timeout_s=3)
            self.assertEqual(driver.wait(timeout_s=3)['status'],'UNKNOWN')

if __name__=='__main__':unittest.main()
