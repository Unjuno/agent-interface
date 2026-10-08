"""Synthetic custody units, not fresh-app experiment results."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit import inspect, expected_rows


def dump(path,value):
    path.write_bytes((json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_packet(root):
    source=root/'source';data=root/'data';source.mkdir();data.mkdir()
    fixture={'schema':'issue5260-a07-focus-probe-effect-construction-v1','allocation':'synthetic-only',
        'seed':52607026,'replicates_per_cell':2,'payload':'hxy','inter_key_gap_ms':20,
        'save_delay_after_last_key_ms':250,'busy_worker_duration_ms':2200,'private_display':':97'}
    dump(source/'fixture.json',fixture)
    freeze={'sha256':{'fixture.json':digest(source/'fixture.json')},'image':{'id':'synthetic-image'}}
    dump(source/'FREEZE.json',freeze);rows=[]
    for index,plan in enumerate(expected_rows(fixture)):
        directory=data/f'row-{index:03d}';directory.mkdir();token=f'synthetic-only:row-{index:03d}'
        pid=100+index
        g={'root_id':10,'target_id':11,'root_width':520,'root_height':250,
           'root_x':0,'root_y':0,'target_x':10,'target_y':20,
           'target_root_x':10,'target_root_y':20,'target_width':100,'target_height':20,
           'save_root_x':10,'save_root_y':70,'save_width':80,'save_height':20}
        witness={'scheduled':1,'focus_callbacks':1,'finalizations':1}
        baseline={'path':'baseline.xwd','exit':0,'started_ns':10,'completed_ns':20}
        (directory/'baseline.xwd').write_bytes(b'synthetic-frame-unit-only')
        baseline.update(sha256=digest(directory/'baseline.xwd'),bytes=(directory/'baseline.xwd').stat().st_size)
        focus=[{'kind':'FocusIn','widget':'decoy','monotonic_ns':5,'sequence':1},
               {'kind':'FocusIn','widget':'target','monotonic_ns':170,'sequence':2}]
        mapped=[{'kind':'Map','monotonic_ns':2},{'kind':'Configure','monotonic_ns':3},focus[0]]
        ready={'geometry':g,'pid':pid,'token':token,'map_configure_events':copy.deepcopy(mapped),
               'baseline_frame':baseline,'ready_ns':30,'readiness':witness}
        binding={'token':token,'pid':pid,'target_id':11}
        state={**binding,'widget':'target','sequence':2,'event_ns':170}
        ack={**state,'schema':'issue5260-a07-focus-ack-v1','focus_get':'target','written_ns':171}
        trace={'mode':plan['instrumentation_mode'],'events':copy.deepcopy(focus),
               'publications':[],'last_state':state,'ack':ack,
               'callbacks':[{'event_sequence':1,'started_ns':5,'completed_record_ns':6},
                            {'event_sequence':2,'started_ns':170,'completed_record_ns':172}]}
        if plan['instrumentation_mode']=='SYNC_FILE':
            trace['callbacks'][0]['completed_record_ns']=12
            trace['callbacks'][1]['completed_record_ns']=196
            entries=[('focus_state.json',1,{**binding,'widget':'decoy','sequence':1,'event_ns':5},6),
                     ('focus_state.json',2,state,180),('focus_ack.json',2,ack,190)]
            for name,sequence,value,start in entries:
                dump(directory/name,value)
                writer={'path':name,'started_ns':start+1,'flushed_ns':start+2,'fsynced_ns':start+3,
                    'replace_started_ns':start+4,'replace_finished_ns':start+5,
                    'sha256':digest(directory/name),'bytes':(directory/name).stat().st_size}
                trace['publications'].append({'path':name,'event_sequence':sequence,'started_ns':start,
                    'completed_ns':start+6,'writer_trace':writer})
        keys=[{'index':i,'char':char,'keycode':40+i,'request_started_ns':200+i*20_000_001,
               'sync_returned_ns':201+i*20_000_001} for i,char in enumerate('hxy')]
        save_start=keys[-1]['sync_returned_ns']+250_000_000
        events=mapped+[focus[1]]+[{'kind':'KeyPress','widget':'target','char':key['char'],
                 'monotonic_ns':key['request_started_ns']+10} for key in keys]
        events.append({'kind':'Save','widget':'target','monotonic_ns':save_start+10})
        visual={'path':'first_visual.xwd','exit':0,'started_ns':220,'completed_ns':230}
        (directory/'first_visual.xwd').write_bytes(b'synthetic-first-frame-unit-only')
        visual.update(sha256=digest(directory/'first_visual.xwd'),bytes=(directory/'first_visual.xwd').stat().st_size)
        first={'schema':'issue5260-first-visual-v1','widget':'target','frame':visual,'observed_ns':231}
        app={'schema':'issue5260-tk-app-v1','pid':pid,'token':token,
            'instrumentation_mode':plan['instrumentation_mode'],'events':events,'focus_trace':trace,
            'ready_snapshot':copy.deepcopy(ready),'geometry':g,'baseline_frame':baseline,
            'ready_ns':30,'readiness':witness,'ended_ns':save_start+100,'first_visual':first,
            'first_key_widget':'target','first_key_ns':211,'save_count':1,
            'saved_text':'hxy','final_target':'hxy','final_decoy':''}
        injection={'click_widget':'target','x':60,'y':30,'click_started_ns':100,'click_sync_returned_ns':150,
            'gate':{'status':'ADMITTED','ack':None,'state':None,'decided_ns':160,'mode':'NO_ACK_CONTROL'},
            'key_requests':keys,'save_requests':[{'x':50,'y':80,'request_started_ns':save_start,
                                                 'sync_returned_ns':save_start+1}]}
        worker=({'pid':200+index,'exit':0,'stderr':'','start_ns':1,'end_ns':2_200_000_001,
             'stdout':json.dumps({'start_ns':1,'end_ns':2_200_000_001})}
             if plan['load']=='cpu_busy' else {'pid':None,'exit':None})
        row={'index':index,**plan,'token':token,'app_pid':pid,'app_exit':0,'app_stderr':'',
             'app_stdout':json.dumps(app),'app_start_ns':1,'app_end_ns':save_start+101,
             'app':app,'ready':ready,'worker':worker,'injection':injection}
        for name,value in (('app_result.json',app),('ready.json',ready),('first_visual.json',first)):
            dump(directory/name,value)
        rows.append(row)
    raw={'schema':fixture['schema'],'allocation':fixture['allocation'],'fixture':fixture,
        'fixture_sha256':digest(source/'fixture.json'),'freeze_sha256':digest(source/'FREEZE.json'),
        'source_sha256':freeze['sha256'],'schedule':expected_rows(fixture),'rows':rows,
        'environment':{'image_id':'synthetic-image','display':':97','tk':8.6,'container_id':'synthetic',
            'python':'3.13.5 synthetic unit','private_exit':{'openbox':0,'xvfb':0},
            'keymap':{'set':{'exit':0},'query':{'exit':0,'stdout':'layout: us'}}}}
    path=data/'candidate_stdout.json';dump(path,raw)
    (data/'candidate_exit.txt').write_text('0\n')
    return path,data,source,raw


class PacketAuditTests(unittest.TestCase):
    def run_case(self,mutate=None):
        with tempfile.TemporaryDirectory() as directory:
            path,data,source,raw=synthetic_packet(Path(directory))
            if mutate:mutate(raw,data,source);dump(path,raw)
            return inspect(path,data,source)

    def test_synthetic_eight_row_custody_accepts_without_gui(self):
        result=self.run_case()
        self.assertEqual(result['errors'],[],result)
        self.assertEqual(result['status'],'METHOD_PASS_CONSTRUCTION_ONLY')
        self.assertEqual(result['hypothesis'],'DESCRIPTIVE_ONLY_NO_EFFICACY_THRESHOLD')

    def test_source_image_schedule_and_identity_corruptions_refused(self):
        for mutate in (lambda r,d,s:r.update(freeze_sha256='0'*64),
                       lambda r,d,s:r['environment'].update(image_id='wrong'),
                       lambda r,d,s:r['rows'].pop(),
                       lambda r,d,s:r['rows'][0].update(app_pid=True),
                       lambda r,d,s:r['rows'][0].update(app_stderr='Exception in Tkinter callback'),
                       lambda r,d,s:r['rows'][0].update(app_stdout='{}')):
            result=self.run_case(mutate)
            self.assertTrue(result['errors'],result)

    def test_actual_readiness_frame_and_app_file_corruptions_refused(self):
        for name in ('ready.json','app_result.json','first_visual.json','baseline.xwd','first_visual.xwd'):
            result=self.run_case(lambda r,d,s:(d/'row-000'/name).write_bytes(b'{}'))
            self.assertTrue(result['errors'],name)


if __name__=='__main__':unittest.main()
