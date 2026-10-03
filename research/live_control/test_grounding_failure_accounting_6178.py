import json,tempfile,unittest
from pathlib import Path
from research.live_control.integrated_efficiency_app_server_model_v1 import PersistentGroundingModel
from research.live_control.test_integrated_efficiency_app_server_model_v1 import FakeClient,raw,usage
ROWS=[]
class FailedClient(FakeClient):
    def wait_turn_completed(self,thread_id,turn_id,timeout=120):
        return {'threadId':thread_id,'turn':{'id':turn_id,'status':'failed','items':[],'error':{'message':'inert failure'}}}
class GroundingFailureAccounting(unittest.TestCase):
    def cases(self):
        return [usage(100,20),None,{'last':{}},usage(-1,0)]
    def test_failed_turn_exception_preserves_known_metadata(self):
        for value in self.cases():
            with self.subTest(usage=value),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);workspace=root/'workspace';workspace.mkdir();image=root/'image';image.write_bytes(b'inert')
                client=FailedClient([raw(100,500)],[value]);model=PersistentGroundingModel(root/'session',workspace,node='unused',cli='unused',client=client,path_converter=str)
                with self.assertRaises(RuntimeError) as caught:model.call(root/'call','inert',image,'compiled',workspace)
                error=caught.exception;failure=json.loads((root/'call/failure.json').read_bytes())
                self.assertEqual(error.call_id,'turn-1');self.assertEqual(error.thread_id,'thread-1')
                self.assertEqual(error.usage,failure['usage']);self.assertEqual(error.wait_ns,failure['runner_ns']);self.assertEqual(error.visible_images_submitted,1)
                self.assertEqual(client.turn,1);self.assertFalse((root/'call/result.json').exists())
                self.assertEqual(failure['usage'],{'input_tokens':100,'cached_input_tokens':20,'cache_write_input_tokens':0,'output_tokens':20,'reasoning_output_tokens':5} if value==usage(100,20) else None)
