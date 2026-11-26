"""A locally rejected read must not become an unknown remote effect."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import input_owner_rpc_v2 as rpc
from input_owner_service_adapter import OwnedOwnerAdapter

class CapacityAdapterTests(unittest.TestCase):
 def test_known_presend_capacity_refusal_does_not_create_obligation(self):
  adapter=object.__new__(OwnedOwnerAdapter)
  adapter._lock=threading.RLock();adapter._closed=False;adapter._obligation=None
  adapter.owner_id='owner';adapter.service_id='service'
  adapter.client=SimpleNamespace(call=Mock(side_effect=rpc.RpcCapacityExhausted('no request sent')))
  with self.assertRaises(rpc.RpcCapacityExhausted):adapter.call('surface_context',key=41)
  self.assertIsNone(adapter._obligation)
 def test_capacity_rejected_down_does_not_mark_token_as_sent(self):
  adapter=object.__new__(OwnedOwnerAdapter);adapter._lock=threading.RLock();adapter._closed=False;adapter._obligation=None
  adapter.owner_id='owner';adapter.service_id='service';adapter._attempted=set();adapter._records=[]
  lease=SimpleNamespace(intent_token='token');adapter._leases={'token':lease}
  wire={'cancel_requested':False,'focus_invalid':False};adapter._bindings={'token':dict(wire)}
  adapter.control=SimpleNamespace(outcomes={});adapter.client=SimpleNamespace(records=[],call=Mock(side_effect=rpc.RpcCapacityExhausted('no send')))
  with patch.object(rpc,'encode_lease',return_value=wire):
   with self.assertRaises(rpc.RpcCapacityExhausted):adapter.call('down',lease,'a')
  self.assertNotIn('token',adapter._attempted);self.assertIsNone(adapter._obligation)
 def test_dispatched_down_unknown_keeps_attempt_and_obligation(self):
  adapter=object.__new__(OwnedOwnerAdapter);adapter._lock=threading.RLock();adapter._closed=False;adapter._obligation=None
  adapter.owner_id='owner';adapter.service_id='service';adapter._attempted=set();adapter._records=[]
  lease=SimpleNamespace(intent_token='token');adapter._leases={'token':lease}
  wire={'cancel_requested':False,'focus_invalid':False};adapter._bindings={'token':dict(wire)}
  adapter.control=SimpleNamespace(outcomes={})
  def uncertain(operation,lease,key,*,on_dispatch):
   on_dispatch();raise rpc.RpcOutcomeUnknown('sent outcome unknown')
  adapter.client=SimpleNamespace(records=[],call=uncertain)
  with patch.object(rpc,'encode_lease',return_value=wire):
   with self.assertRaises(rpc.RpcOutcomeUnknown):adapter.call('down',lease,'a')
  self.assertIn('token',adapter._attempted);self.assertEqual(adapter._obligation['kind'],'ordinary_rpc_unknown')
if __name__=='__main__':unittest.main()
