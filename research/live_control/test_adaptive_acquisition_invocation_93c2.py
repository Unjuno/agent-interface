import copy,json,unittest
import adaptive_acquisition_caller_v3 as caller
ROWS=[]
def cell(fault,terminal):
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
            return {'call_id':name,'output':output,'usage':None,'requested_model':'E03-inert','requested_effort':'none','cost':cost,'visible_images_submitted':0,'wait_ns':0}
        return callback
    def execute(_):
        trace.append('execute');counts['execute']+=1
        if fault=='typed_execute':raise caller.ModelFailure('E03 entered execute',typed_status='DEFERRED_UPSTREAM')
        return {'status':'completed'}
    def verify(_):trace.append('verify');counts['verify']+=1;return {'status':'succeeded'}
    adapters={'observe_source':local('observe',{'id':'source'}),'coarse_model':model('coarse',.125,{'status':'candidate','id':'coarse'}),'acquire_anchor':local('anchor',{'id':'anchor'}),'anchor_model':model('target',.25,{'status':'target_reference','target':{'id':'fixed'}}),'final_revalidate':local('revalidate',{'status':'revalidated'}),'execute':execute,'verify_effect':verify,'journal':journal}
    if fault=='missing':del adapters['execute']
    if fault=='noncallable':adapters['execute']=42
    spec={'target':'E03 target','route':'cold','coarse_origin':'model_produced','provided_coarse':None,'cached_target':None,'local_repair_on':[],'repair_on':[],'session_id':'E03-inert'}
    result=caller.run(spec,adapters,clock=clock,id_factory=iter(['coarse-attempt','target-attempt']).__next__)
    row={'fault':fault,'terminal':terminal,'counts':counts,'trace':trace,'events':events,'result':result};ROWS.append(row);return row
class InvocationBoundary(unittest.TestCase):
    def test_precise_invocation_boundary(self):
        for fault in ['healthy','start_clock','start_journal','missing','noncallable','typed_execute']:
            for terminal in [False,True]:
                with self.subTest(fault=fault,terminal=terminal):
                    row=cell(fault,terminal);r=row['result'];entered=fault in {'healthy','typed_execute'};healthy=fault=='healthy'
                    self.assertEqual(row['counts'],{'execute':int(entered),'verify':int(healthy),'model':2,'terminal':1})
                    self.assertEqual(r['input_authority'],'consumed_by_recorded_execute_stage' if entered else 'none')
                    self.assertEqual(r['delivery'],'confirmed' if healthy else 'delivery_uncertain' if entered else None)
                    self.assertEqual(r['execution_progress'],{'status':'completed'} if healthy else None)
                    self.assertEqual(r['task_effect'],'succeeded' if healthy else None)
                    self.assertEqual(r['outcome'],'TASK_SUCCEEDED' if healthy and not terminal else 'CALLER_FAILED')
                    self.assertEqual(r['accounting']['cost'],.375)
                    self.assertEqual([x['cost'] for x in r['model_call_ledger']],[.125,.25])
                    json.dumps(r,allow_nan=False)
