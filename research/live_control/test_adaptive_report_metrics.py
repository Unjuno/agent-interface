"""All-attempt report metrics; actual caller and selected consumer AST, no GUI/model."""
import ast
import json
import os
import unittest
from pathlib import Path
import adaptive_acquisition_caller_v3 as c

source=Path(os.environ.get('CONSUMER_SOURCE',Path(__file__).with_name('adaptive_semantic_repair_live_v2.py'))).read_bytes()
parsed=ast.parse(source)
assignments=[n for n in ast.walk(parsed) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'completed_model_records','total_input','metrics'} for t in n.targets)]
if len(assignments)!=3:raise RuntimeError('exact three consumer source statements required')
code=compile(ast.Module(body=sorted(assignments,key=lambda n:n.lineno),type_ignores=[]),'selected-exact-consumer-metrics','exec')
rows=[]
class Tests(unittest.TestCase):
    def cell(self,name):
        sent=[]
        target={'handle':'own-save','point':[1,2]}
        usage={field:0 for field in c.USAGE_FIELDS};usage['input_tokens']=5
        def model(payload):
            sent.append(name)
            metadata={} if name=='unknown' else {'usage':usage,'visible_images_submitted':0 if name=='known-zero' else 2,'wait_ns':0 if name=='known-zero' else 5000000}
            raise c.ModelFailure('inert attempted model failed',**metadata)
        mapping={'reuse_revalidate':lambda p:{'status':'revalidated' if name=='no-call' else 'association_changed'},'acquire_expansion':lambda p:{'image':'inert'},'expanded_model':model,'final_revalidate':lambda p:{'status':'revalidated'},'execute':lambda p:{'status':'completed'},'verify_effect':lambda p:{'status':'succeeded'}}
        adaptive=c.run({'target':'Save','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,'cached_target':target,'local_repair_on':[],'repair_on':['association_changed'],'session_id':'own-metrics'},mapping)
        namespace={'adaptive':adaptive,'initial_model':{'usage':{'input_tokens':100}},'initial_outcome':{'visible_images_submitted':1},'client':{'exchanges':[]},'recovery_completed_ns':2,'mutation':{'capture_ns':1}}
        exec(code,namespace)
        actual=namespace['metrics']
        expected={'total_model_calls':1 if name=='no-call' else 2,'total_input_tokens':100 if name=='no-call' else None if name=='unknown' else 105,'adaptive_model_wait_ms':None if name=='unknown' else 5.0 if name=='known-positive' else 0.0,'model_visible_images':None if name=='unknown' else 3 if name=='known-positive' else 1}
        row={'case':name,'adaptive':adaptive,'metrics':actual,'expected':expected,'fake_model_attempts':len(sent)};rows.append(row)
        self.assertEqual(len(sent),0 if name=='no-call' else 1)
        for key,value in expected.items():self.assertEqual(actual[key],value,key)
        self.assertEqual(actual['completed_model_calls'],1)
    def test_no_call(self):self.cell('no-call')
    def test_unknown(self):self.cell('unknown')
    def test_known_zero(self):self.cell('known-zero')
    def test_known_positive(self):self.cell('known-positive')

if __name__ == '__main__':
    unittest.main()
