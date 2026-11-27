import tempfile,unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from Xlib import X
from Xlib.ext import xtest
from runtime.cli_v1 import test_mcp_xvfb_blocked_release_integration as fixture

class FixtureIdempotenceTests(unittest.TestCase):
 def test_repeated_get_injects_only_one_delayed_key(self):
  raw=Mock();connection=SimpleNamespace(sync=Mock(),flush=Mock(),display=SimpleNamespace(info=SimpleNamespace(resource_id_base=123)))
  backend=SimpleNamespace(d=connection,_keycode=lambda name:56)
  session=SimpleNamespace(backend=backend)
  owner=SimpleNamespace(get=lambda:session,cancel_guarded=lambda token:{'status':'not_active'})
  with tempfile.TemporaryDirectory() as directory,patch.object(fixture,'GuardedSessionOwner',return_value=owner),patch.object(xtest,'fake_input',raw):
   wrapped=fixture._xvfb_blocking_owner_factory({'app':1},directory,':1',{})
   for _ in range(4):wrapped.get()
   xtest.fake_input(connection,X.KeyPress,detail=38)
   self.assertEqual(raw.call_count,2,'one intended a press plus exactly one injected b press')
   self.assertEqual(raw.call_args_list[0].args[1],X.KeyPress)
   self.assertEqual(raw.call_args_list[1].kwargs['detail'],56)
if __name__=='__main__':unittest.main()
