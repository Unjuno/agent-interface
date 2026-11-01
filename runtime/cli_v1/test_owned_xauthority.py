"""Child-scoped X authority for owned sessions and cancellation supervisor."""
import os
from pathlib import Path
import tempfile
import time
import unittest
import subprocess
import sys
from unittest.mock import patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory

def recording_factory(targets,directory,display_name,options):
    Path(directory).mkdir(parents=True,exist_ok=True)
    (Path(directory)/'child-auth.txt').write_text(os.environ.get('XAUTHORITY','<absent>'))
    return _fake_owner_factory(targets,directory,display_name,options)

def recording_supervisor(request):
    return {'operation_id':request['operation_id'],'session_id':request['session_id'],
            'status':'completed','observed_authority':os.environ.get('XAUTHORITY','<absent>')}

def x_connection_supervisor(request):
    from Xlib import display
    connection=display.Display(request['display']);connection.sync();connection.close()
    return {'operation_id':request['operation_id'],'session_id':request['session_id'],'status':'completed'}

class ChildAuthorityTests(unittest.TestCase):
    def test_explicit_authority_requires_prestarted_cleanup_supervisor(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'prestarted'):
                OwnedGuardedSessionOwner({'app':20},td,xauthority='/tmp/fixture-authority')

    def test_real_private_display_reachable_by_owner_and_supervisor_with_isolated_authority(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        script='''import os,pathlib,time
from Xlib import X,display
d=display.Display();w=d.screen().root.create_window(10,10,120,80,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent);w.map();d.sync()
pathlib.Path(os.environ['READY']).write_text(str(w.id))
while not pathlib.Path(os.environ['STOP']).exists():time.sleep(.01)
d.close()
'''
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{'XAUTHORITY':'parent-sentinel'}):
            root=Path(td);display_owner=PrivateDisplayOwner(root/'display');target=None;owner=None
            try:
                session=display_owner.start(timeout_s=5)
                env=dict(os.environ,DISPLAY=session.display,XAUTHORITY=str(session.authority),READY=str(root/'ready'),STOP=str(root/'stop'))
                target=subprocess.Popen([sys.executable,'-c',script],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                end=time.monotonic()+4
                while not (root/'ready').exists() and time.monotonic()<end and target.poll() is None:time.sleep(.01)
                self.assertTrue((root/'ready').exists(),'target failed to start')
                xid=int((root/'ready').read_text())
                owner=OwnedGuardedSessionOwner({'app':xid},root/'owner',session.display,
                    prestarted_cancel_supervisor=True,_cleanup_supervisor_target=x_connection_supervisor,
                    xauthority=str(session.authority))
                owner.get()
                result=owner._cleanup_supervisor.run({'operation_id':'probe','session_id':owner.session_id,'display':session.display},deadline_monotonic_ns=time.monotonic_ns()+3_000_000_000)
                self.assertEqual(result['status'],'completed');self.assertEqual(os.environ['XAUTHORITY'],'parent-sentinel')
            finally:
                if owner is not None:owner.close()
                if target is not None:
                    (root/'stop').touch()
                    try:target.wait(timeout=3)
                    except subprocess.TimeoutExpired:target.terminate();target.wait(timeout=3)
                display_owner.close()

    def test_owned_and_cleanup_children_use_explicit_authority_without_parent_mutation(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{'XAUTHORITY':'parent-sentinel'}):
            root=Path(td);authority=root/'private-authority';authority.write_bytes(b'fixture')
            try:
                owner=OwnedGuardedSessionOwner({'app':20},root/'owner',process_identity=True,query_worker=True,
                    prestarted_cancel_supervisor=True,_owner_factory=recording_factory,
                    _cleanup_supervisor_target=recording_supervisor,xauthority=str(authority))
            except TypeError as e:self.fail('explicit child authority unavailable: '+str(e))
            try:
                owner.get()
                self.assertEqual((root/'owner'/'child-auth.txt').read_text(),str(authority))
                result=owner._cleanup_supervisor.run({'operation_id':'probe','session_id':owner.session_id},
                    deadline_monotonic_ns=time.monotonic_ns()+3_000_000_000)
                self.assertEqual(result['status'],'completed');self.assertEqual(result['observed_authority'],str(authority))
                self.assertEqual(os.environ['XAUTHORITY'],'parent-sentinel')
            finally:owner.close()

if __name__=='__main__':unittest.main()
