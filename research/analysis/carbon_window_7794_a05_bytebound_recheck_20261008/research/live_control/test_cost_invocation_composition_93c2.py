import copy,json,unittest
import adaptive_acquisition_caller_v3 as caller
ROWS=[]
def cell(fault,terminal,costs,failed_stage=None,failed_cost_known=False):
    counts={'execute':0,'verify':0,'model':0,'terminal':0};tick=0;events=[];trace=[]
    def clock():
        nonlocal tick
        tick+=1
        if fault=='start_clock' and tick==11:raise RuntimeError('E03 start clock')
        return tick*10
    def journal(e):
        events.append(copy.deepcopy(e))
        if fault=='start_journal' and e.get('stage')=='execute' and e.get('event')=='stage_started':raise RuntimeError('E03 start journal')
        if e.get('event')=='adaptive_route_finished':
            counts['terminal']+=1
            if terminal:raise RuntimeError('E03 terminal journal')
    def local(name,value):
        def callback(_):trace.append(name);return copy.deepcopy(value)
        return callback
    def model(name,cost,output):
        def callback(_):
            trace.append(name);counts['model']+=1
            if name==failed_stage:
                error=caller.ModelFailure('I08 failed model',typed_status='DEFERRED_UPSTREAM')
                if failed_cost_known:error.cost=1.25
                raise error
            return {'call_id':name,'output':output,'usage':None,'requested_model':'E03-inert','requested_effort':'none','cost':cost,'visible_images_submitted':0,'wait_ns':0}
        return callback
    def execute(_):
        trace.append('execute');counts['execute']+=1
        if fault=='typed_execute':raise caller.ModelFailure('E03 entered execute',typed_status='DEFERRED_UPSTREAM')
        return {'status':'completed'}
    def verify(_):trace.append('verify');counts['verify']+=1;return {'status':'succeeded'}
    adapters={'observe_source':local('observe',{'id':'source'}),'coarse_model':model('coarse',costs[0],{'status':'candidate','id':'coarse'}),'acquire_anchor':local('anchor',{'id':'anchor'}),'anchor_model':model('target',costs[1],{'status':'target_reference','target':{'id':'fixed'}}),'final_revalidate':local('revalidate',{'status':'revalidated'}),'execute':execute,'verify_effect':verify,'journal':journal}
    if fault=='missing':del adapters['execute']
    if fault=='noncallable':adapters['execute']=42
    spec={'target':'E03 target','route':'cold','coarse_origin':'model_produced','provided_coarse':None,'cached_target':None,'local_repair_on':[],'repair_on':[],'session_id':'E03-inert'}
    result=None;escaped=None
    try:result=caller.run(spec,adapters,clock=clock,id_factory=iter(['coarse-attempt','target-attempt']).__next__)
    except Exception as error:escaped=repr(error)
    row={'fault':fault,'terminal':terminal,'counts':counts,'trace':trace,'events':events,'result':result,'escaped':escaped,'costs':costs,'failed_stage':failed_stage,'failed_cost_known':failed_cost_known};ROWS.append(row);return row
class CostInvocationComposition(unittest.TestCase):
    def test_joint_faults(self):
        for vector,costs in [('finite',[.125,.25]),('missing',[None,.25]),('overflow',[1e308,1e308]),('huge',[10**500,.25])]:
            for fault in ['healthy','start_clock','start_journal','missing','noncallable','typed_execute']:
                for terminal in [False,True]:
                    with self.subTest(vector=vector,fault=fault,terminal=terminal):
                        row=cell(fault,terminal,costs);self.assertIsNone(row['escaped']);r=row['result'];entered=fault in {'healthy','typed_execute'};healthy=fault=='healthy'
                        self.assertEqual(row['counts'],{'execute':int(entered),'verify':int(healthy),'model':2,'terminal':1})
                        self.assertEqual(r['input_authority'],'consumed_by_recorded_execute_stage' if entered else 'none')
                        self.assertEqual(r['delivery'],'confirmed' if healthy else 'delivery_uncertain' if entered else None)
                        self.assertEqual(r['execution_progress'],{'status':'completed'} if healthy else None)
                        self.assertEqual(r['task_effect'],'succeeded' if healthy else None)
                        self.assertEqual(r['outcome'],'TASK_SUCCEEDED' if healthy and not terminal else 'CALLER_FAILED')
                        self.assertEqual(r['accounting']['cost'],.375 if vector=='finite' else None)
                        self.assertEqual([x['cost'] for x in r['model_call_ledger']],costs)
                        json.dumps(r,allow_nan=False)
    def test_failed_attempts(self):
        for stage in ['coarse','target']:
            for known in [False,True]:
                for terminal in [False,True]:
                    with self.subTest(stage=stage,known=known,terminal=terminal):
                        row=cell('healthy',terminal,[.125,.25],stage,known);self.assertIsNone(row['escaped']);r=row['result'];attempted=1 if stage=='coarse' else 2
                        self.assertEqual(row['counts'],{'execute':0,'verify':0,'model':attempted,'terminal':1})
                        self.assertEqual(r['input_authority'],'none');self.assertIsNone(r['delivery']);self.assertIsNone(r['execution_progress']);self.assertIsNone(r['task_effect']);self.assertIsNone(r['accounting']['cost'])
                        self.assertEqual(r['accounting']['attempted_calls'],attempted);self.assertEqual(r['accounting']['completed_calls'],attempted-1)
                        self.assertEqual(r['outcome'],'CALLER_FAILED' if terminal else 'TASK_DEFERRED')
                        json.dumps(r,allow_nan=False)
