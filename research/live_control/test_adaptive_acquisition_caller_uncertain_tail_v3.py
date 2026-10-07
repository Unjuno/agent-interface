import copy,json,pathlib,unittest
import adaptive_acquisition_caller_v3 as caller
R=pathlib.Path(__file__).resolve().parent/'caller_uncertain_tail_I13'
RECORDS=[]
def execute(value):
    counts={'execute':0,'verify':0};events=[]
    def invoke(_):counts['execute']+=1;return copy.deepcopy(value)
    def verify(_):counts['verify']+=1;return {'status':'succeeded'}
    spec=json.loads((R/'LIVE_CALLER.json').read_text(encoding='utf-8'))['spec']
    result=caller.run(spec,{'reuse_revalidate':lambda _:{'status':'revalidated'},'final_revalidate':lambda _:{'status':'revalidated'},
        'execute':invoke,'verify_effect':verify,'journal':events.append},clock=lambda:0)
    RECORDS.append({'input':value,'counts':counts,'events':events,'result':result})
    return result,counts
class Tail(unittest.TestCase):
    def test_retained_real_browser_execution_receipt(self):
        value=json.loads((R/'RESPONSE3.json').read_text(encoding='utf-8'))['decision']
        result,counts=execute(value)
        self.assertEqual(result['execution_progress'],value)
        self.assertEqual(counts,{'execute':1,'verify':0})
        self.assertEqual(result['outcome'],'EXECUTION_INCOMPLETE')
        self.assertEqual(result['delivery'],'delivery_uncertain')
        self.assertEqual(result['input_authority'],'consumed_by_recorded_execute_stage')
    def test_uncertain_tail_and_explicit_no_input_controls(self):
        for reason in ('delivery_uncertain','execution_failed'):
            for count in (0,1,7):
                for marker in ('absent',True,False):
                    if marker is False and count:continue
                    value={'status':'safe_yield','reason':reason,'completed_actions':count}
                    if marker!='absent':value['input_dispatched']=marker
                    result,counts=execute(value)
                    self.assertEqual(result['execution_progress'],value)
                    self.assertEqual(counts,{'execute':1,'verify':0})
                    self.assertEqual(result['delivery'],'not_attempted' if marker is False else 'delivery_uncertain')
                    self.assertEqual(result['input_authority'],'none' if marker is False else 'consumed_by_recorded_execute_stage')
                    self.assertEqual(result['accounting']['attempted_calls'],0)
