import copy
import json
import unittest
from effect_audit import effect_errors,worker_errors


FIXTURE={'payload':'hxy','inter_key_gap_ms':20,'save_delay_after_last_key_ms':250,
         'busy_worker_duration_ms':2200}


def refused():
    return {'load':'idle','worker':{'pid':None,'exit':None},
        'ready':{'geometry':{'target_root_x':10,'target_root_y':20,'target_width':100,
            'target_height':20,'decoy_root_x':10,'decoy_root_y':5,'decoy_width':100,
            'decoy_height':20,'save_root_x':10,'save_root_y':50,'save_width':40,'save_height':20}},
        'injection':{'click_widget':'decoy','x':60,'y':15,'click_started_ns':100,
            'gate':{'status':'REFUSED','decided_ns':500_000_100},'key_requests':[],'save_requests':[]},
        'app':{'events':[],'save_count':0,'saved_text':None,'final_target':'','final_decoy':'','ended_ns':600_000_100}}


class EffectTests(unittest.TestCase):
    def test_admitted_literal_input_events_and_field_values_match(self):
        row=refused();injection=row['injection'];app=row['app']
        injection.update(click_widget='target',x=60,y=30,
                         gate={'status':'ADMITTED','decided_ns':110})
        injection['key_requests']=[{'index':i,'char':char,'keycode':20+i,
            'request_started_ns':120+i*20_000_001,'sync_returned_ns':121+i*20_000_001}
            for i,char in enumerate('hxy')]
        app['events']=[{'kind':'KeyPress','char':char,'widget':'target',
            'monotonic_ns':122+i*20_000_001} for i,char in enumerate('hxy')]
        injection['save_requests']=[{'x':30,'y':60,'request_started_ns':290_000_123,
                                    'sync_returned_ns':290_000_124}]
        app['events'].append({'kind':'Save','monotonic_ns':290_000_125})
        app.update(save_count=1,saved_text='hxy',final_target='hxy',first_key_widget='target',first_key_ns=123)
        self.assertEqual(effect_errors(row,FIXTURE),[])
        app['saved_text']='xy'
        self.assertIn('effect_binding',effect_errors(row,FIXTURE))

    def test_literal_refusal_is_zero_input_and_effect(self):
        self.assertEqual(effect_errors(refused(),FIXTURE),[])

    def test_refusal_cannot_hide_actual_input_or_effect(self):
        changes=[lambda r:r['app']['events'].append({'kind':'KeyPress'}),
            lambda r:r['app'].update(save_count=1),lambda r:r['app'].update(final_decoy='h'),
            lambda r:r['injection']['key_requests'].append({}),
            lambda r:r['injection'].update(x=61)]
        for index,change in enumerate(changes):
            row=refused();change(row)
            with self.subTest(index=index):self.assertTrue(effect_errors(row,FIXTURE))

    def test_busy_refusal_requires_entire_click_to_decision_coverage(self):
        row=refused();row['load']='cpu_busy'
        row['worker']={'pid':20,'exit':0,'stderr':'','start_ns':90,'end_ns':2_200_000_090,
            'stdout':json.dumps({'start_ns':90,'end_ns':2_200_000_090})}
        self.assertEqual(worker_errors(row,FIXTURE),[])
        row['worker']['start_ns']=101
        self.assertTrue(worker_errors(row,FIXTURE))

    def test_busy_worker_receipt_must_match_actual_stdout(self):
        row=refused();row['load']='cpu_busy'
        row['worker']={'pid':20,'exit':0,'stderr':'','start_ns':90,'end_ns':2_200_000_090,'stdout':'{}'}
        self.assertTrue(worker_errors(row,FIXTURE))


if __name__=='__main__':unittest.main()
