"""Ordinary retained-data regressions for three review findings; no browser imports."""
import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
CLIENT=json.loads((ROOT/'inputs/client.json').read_bytes())
SERVER=json.loads((ROOT/'inputs/server.json').read_bytes())
def specifications():
    specs=[]
    for i,row in enumerate(CLIENT['rows']):
        specs.append({'label':f'cohort-zero/{i}','input':'client','operations':[
          {'path':['rows',i,'ended_ns'],'value':row['offered_ns']},{'path':['rows',i,'elapsed_ns'],'value':'0'}]})
    for i,event in enumerate(SERVER['events']):
        if event['event']=='case_closed':
            specs.append({'label':f'close-float/{i}','input':'server','operations':[{'path':['events',i,'generation'],'value':float(event['generation'])}]})
            if event['generation']==1:specs.append({'label':f'close-bool/{i}','input':'server','operations':[{'path':['events',i,'generation'],'value':True}]})
    for i,row in enumerate(CLIENT['rows']):
        for j,event in enumerate(row['events']):
            if event['event']=='delivered':specs.append({'label':f'delivery-absent/{i}/{j}','input':'client','operations':[{'path':['rows',i,'events',j,'read_id'],'value':999999}]})
    assert len(specs)==72
    return specs
def apply(spec):
    c,s=copy.deepcopy(CLIENT),copy.deepcopy(SERVER)
    data=c if spec['input']=='client' else s
    for operation in spec['operations']:
        item=data
        for key in operation['path'][:-1]:item=item[key]
        item[operation['path'][-1]]=copy.deepcopy(operation['value'])
    return c,s
def extra_copies():
    result=[]
    def add(label,change):
        c,s=copy.deepcopy(CLIENT),copy.deepcopy(SERVER);change(c,s);result.append((label,c,s))
    def event(c,kind):return next(e for e in c['rows'][0]['events'] if e['event']==kind)
    add('delivery-float-alias',lambda c,s:event(c,'delivered').update(read_id=1.0))
    add('delivery-bool-alias',lambda c,s:event(c,'delivered').update(read_id=True))
    add('delivery-scope',lambda c,s:event(c,'delivered')['scope'].update(target='B'))
    add('decision-read',lambda c,s:event(c,'decision').update(read_id=999999))
    add('decision-time',lambda c,s:event(c,'decision').update(ns_decision=str(int(c['rows'][0]['consumers'][0]['decision_ns'])+1)))
    add('start-deadline',lambda c,s:event(c,'waiter_start').update(deadline_ns=str(int(c['rows'][0]['consumers'][0]['deadline_ns'])+1)))
    add('start-scope',lambda c,s:event(c,'waiter_start')['scope'].update(target='B'))
    add('start-request',lambda c,s:event(c,'waiter_start').update(request='outside'))
    add('missing-delivery',lambda c,s:c['rows'][0]['events'].remove(event(c,'delivered')))
    add('duplicate-delivery',lambda c,s:c['rows'][0]['events'].append(copy.deepcopy(event(c,'delivered'))))
    add('cohort-start-after-waiter',lambda c,s:c['rows'][0].update(offered_ns=c['rows'][0]['consumers'][0]['decision_ns'],elapsed_ns=str(int(c['rows'][0]['ended_ns'])-int(c['rows'][0]['consumers'][0]['decision_ns']))))
    add('cohort-end-before-last-event',lambda c,s:c['rows'][0].update(ended_ns=c['rows'][0]['consumers'][0]['ended_ns'],elapsed_ns=str(int(c['rows'][0]['consumers'][0]['ended_ns'])-int(c['rows'][0]['offered_ns']))))
    return result
class ReviewRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.candidate=load(ROOT/'audit_v2.py')
    def test_original_still_reconciles_all_effects_and_reads(self):
        result=self.candidate.audit(CLIENT,SERVER)
        self.assertEqual(result['errors'],[])
        self.assertEqual([result['summary'][p]['offered_reads'] for p in ('independent','predicate','scoped')],[10,6,8])
        self.assertEqual([result['summary'][p]['correct_effects'] for p in ('independent','predicate','scoped')],[9,7,9])
        self.assertIs(result['equivalent_cohort_latency_gain_observed'],True)
    def test_all_72_review_family_copies_reject(self):
        for spec in specifications():
            with self.subTest(label=spec['label']):self.assertTrue(self.candidate.audit(*apply(spec))['errors'])
    def test_extra_join_and_interval_regressions_reject(self):
        for label,c,s in extra_copies():
            with self.subTest(label=label):self.assertTrue(self.candidate.audit(c,s)['errors'])
    def test_existing_12_controls_remain_effective(self):
        controls=self.candidate.controls(CLIENT,SERVER)
        self.assertEqual(len(controls),12);self.assertTrue(all(c['rejected'] for c in controls))
if __name__=='__main__':unittest.main(verbosity=2)
