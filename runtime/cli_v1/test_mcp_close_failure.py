import tempfile,unittest
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import FakeX

class CloseFailure(unittest.IsolatedAsyncioTestCase):
    async def test_worker_close_failure_consumes_bridge_authority(self):
        fake=FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            await server.call_tool('interface_guarded_observe',{})
            bridge=fake.backend.owner;bridge.session.recovery_required=True
            def fail():raise RuntimeError('injected worker close failure')
            bridge.stop_target_queries=fail
            try:await server.call_tool('interface_close',{})
            except Exception:pass
            before=list(fake.emissions);row=bridge.recover_input(bridge.binding_revision)
            self.assertEqual(row.get('error'),'RECOVERY_REQUIRES_OPEN_SESSION',row)
            self.assertFalse(row['release_attempted']);self.assertEqual(fake.emissions,before)
if __name__=='__main__':unittest.main(verbosity=2)
