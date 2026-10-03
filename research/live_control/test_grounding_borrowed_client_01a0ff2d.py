import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from research.live_control import integrated_efficiency_app_server_model_v1 as model
ROWS=[]
class FalseClient:
    def __bool__(self):return False
    def close(self):raise RuntimeError('borrowed client must not be closed')
class FalseBorrowedTest(unittest.TestCase):
    def test_false_borrowed_client_is_used_without_factory_or_close(self):
        client=FalseClient();factory=[]
        class Planner:
            def __init__(self,actual,**kw):self.actual=actual
            def start_session(self):return 'thread-fixture'
        def forbidden(*a,**kw):factory.append(True);raise RuntimeError('owned factory unexpectedly used')
        observed=None;obj=None
        with tempfile.TemporaryDirectory() as tmp,patch.object(model,'PersistentPlannerAdapter',Planner),patch.object(model,'CodexAppServerClient',forbidden):
            try:obj=model.PersistentGroundingModel(Path(tmp)/'session',tmp,node='inert',cli='inert',client=client,path_converter=str)
            except BaseException as error:observed=error
            ROWS.append({'factory_calls':len(factory),'error':None if observed is None else repr(observed),'same_borrowed_client':obj is not None and obj.client is client,'borrowed_truthiness':bool(client)})
            self.assertIsNone(observed);self.assertEqual(factory,[]);self.assertIs(obj.client,client);self.assertIs(obj.planner.actual,client);obj.close()
if __name__ == '__main__':
    unittest.main(verbosity=2)
