"""Actual activation request boundary and release, with Fake X transport only."""
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from runtime.backends.x11_v1.backend import X11Backend
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import metadata
from .bridge import NativeHandleBridge


class ActivationFenceTests(unittest.TestCase):
    def exercise(self,fault):
        fake=FakeX(self);now=[1_000_000];expiry=now[0]+1_000_000_000
        backend=fake.backend
        backend._activation_supported=lambda:True
        backend._window_property=lambda name:[20]
        backend._focus_within=lambda xid:True
        backend.d.intern_atom=lambda name:7
        backend.d.flush=Mock();backend.root.send_event=Mock()
        with tempfile.TemporaryDirectory() as td,patch('time.monotonic_ns',side_effect=lambda:now[0]):
            bridge=NativeHandleBridge(None,{'app':20},'app',td+'/bridge',process_identity=True)
            source=bridge.observe()
            original_target=backend._activation_target
            def target(name):
                window=original_target(name)
                if fault=='deadline': now[0]=expiry
                elif fault=='history': bridge.history.clear()
                elif fault=='target': backend.targets['app']=SimpleNamespace(id=21)
                elif fault=='lease_replacement': bridge.deadline=expiry+1_000_000_000
                return window
            backend._activation_target=target
            if fault=='generation': fake.generation='b'*64
            original_read=bridge._read_process_identity
            def read():
                value=original_read()
                if fault=='identity_deadline': now[0]=expiry
                return value
            bridge._read_process_identity=read
            try:
                result=bridge.activate_window(window_id=20,source_sequence=source['sequence'],
                    current_binding_revision=bridge.binding_revision,expires_at_ns=expiry,timeout_ms=100)
                if fault=='healthy':
                    self.assertEqual(result['status'],'completed',result)
                    backend.root.send_event.assert_called_once();backend.d.flush.assert_called_once()
                else:
                    self.assertEqual(result['status'],'execution_failed',result)
                    backend.root.send_event.assert_not_called();backend.d.flush.assert_not_called()
                    self.assertFalse(result['execution']['activations'][0]['request_attempted'])
                self.assertTrue(bridge.review_required)
                self.assertTrue(result['execution']['releases'][-1]['verified'])
                self.assertEqual(fake.emissions,[])
                self.assertIsNone(bridge.active);self.assertIsNone(bridge.deadline)
            finally: bridge.close()

    def test_healthy_explicit_activation_still_sends_once(self): self.exercise('healthy')
    def test_changed_process_generation_never_sends_request(self): self.exercise('generation')
    def test_target_lookup_consuming_original_expiry_never_sends(self): self.exercise('deadline')
    def test_identity_lookup_consuming_original_expiry_never_sends(self): self.exercise('identity_deadline')
    def test_invalidated_history_at_request_boundary_never_sends(self): self.exercise('history')
    def test_changed_target_at_request_boundary_never_sends(self): self.exercise('target')
    def test_replaced_original_deadline_at_request_boundary_never_sends(self): self.exercise('lease_replacement')


class MCPActivationSourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_recovery_cannot_relabel_invalidated_source_then_fresh_source_can_activate(self):
        fake=FakeX(self);backend=fake.backend
        backend._activation_supported=lambda:True;backend._window_property=lambda name:[20]
        backend._focus_within=lambda xid:True;backend.d.intern_atom=lambda name:7
        backend.d.flush=Mock();backend.root.send_event=Mock()
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11',guarded_process_identity=True)
            try:
                source=metadata(await server.call_tool('interface_guarded_observe',{}))
                bridge=backend.owner;bridge.session.recovery_required=True
                recovered=metadata(await server.call_tool('interface_guarded_recover_input',dict(
                    current_binding_revision=source['session']['binding_revision'])))
                self.assertEqual(recovered['status'],'input_recovered')
                arguments=dict(window_id=20,source_sequence=source['source']['sequence'],
                    current_binding_revision=recovered['binding_revision'],
                    expires_at_ns=time.monotonic_ns()+1_000_000_000,timeout_ms=100)
                refused=metadata(await server.call_tool('interface_guarded_activate_window',arguments))
                self.assertEqual(refused['status'],'refused',refused)
                backend.root.send_event.assert_not_called()
                fresh=metadata(await server.call_tool('interface_guarded_observe',{}))
                chosen=metadata(await server.call_tool('interface_guarded_activate_window',dict(arguments,
                    source_sequence=fresh['source']['sequence'],expires_at_ns=time.monotonic_ns()+1_000_000_000)))
                self.assertEqual(chosen['status'],'completed',chosen)
                backend.root.send_event.assert_called_once()
                self.assertTrue(chosen['session']['review_required'])
                self.assertEqual(fake.emissions,[])
            finally: await server.call_tool('interface_close',{})
