"""Synthetic byte/file packet construction; never starts candidate or GUI."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit import inspect,expected_rows
from test_full_input import full_row

def dump(path,value):path.write_bytes((json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def packet(root):
    source=root/'source';data=root/'data';source.mkdir();data.mkdir()
    fixture={'schema':'a12-synthetic-only','allocation':'synthetic-a12','seed':52612026,
        'tasks':[{'id':'compact','payload':'hmt','geometry':'520x250+80+70'},
            {'id':'offset','payload':'hns','geometry':'580x270+140+100'}],
        'private_display':':97','ack_timeout_ms':500,'drift_timeout_ms':500,'ack_max_age_ms':50,
        'inter_key_gap_ms':0,'save_delay_after_last_key_ms':0}
    dump(source/'fixture.json',fixture)
    for name in ('app.py','candidate.py','audit.py','input_audit_a12.py','task_file.py','task_file_audit.py',
            'recovery.py','recovery_audit.py','recovery_phase.py','drift.py','drift_audit.py','gate_audit.py',
            'effect_audit.py','pipe_audit.py','pipe_gate.py','pipe_receipt.py','pipe_transport.py','focus_pipe.py',
            'focus_trace.py','private_cache.py','cache_audit.py','ready_guard.py','readiness_once.py',
            'sample_custody.py','common_a08_audit.py'):
        (source/name).write_bytes(b'# synthetic source custody only; not executed\n')
    freeze={'sha256':{p.name:digest(p) for p in source.iterdir()},'image':{'id':'synthetic-image'}}
    dump(source/'FREEZE.json',freeze);frozen=digest(source/'FREEZE.json');rows=[]
    for index,plan in enumerate(expected_rows(fixture)):
        row=full_row();row.update(plan,index=index,token=f'synthetic-a12:row-{index:03d}',app_pid=100+index)
        app=row['app'];inj=row['injection'];phase=inj['post_admission'];g=row['ready']['geometry']
        directory=data/f'row-{index:03d}';directory.mkdir()
        g.update(root_id=41,root_width=520,root_height=250,root_x=100,root_y=200,
            target_x=0,target_y=0)
        g['root_width'],g['root_height']=map(int,plan['geometry'].split('+')[0].split('x'))
        focuses=[dict(kind='FocusIn',widget='decoy',monotonic_ns=5,sequence=1),
            dict(kind='FocusIn',widget='target',monotonic_ns=80,sequence=2)]
        if plan['mode']!='STABLE':
            focuses.extend([dict(kind='FocusOut',widget='target',monotonic_ns=120,sequence=3),
                dict(kind='FocusIn',widget='decoy',monotonic_ns=130,sequence=4)])
        if plan['mode']=='DRIFT_RECOVER':
            focuses.extend([dict(kind='FocusOut',widget='decoy',monotonic_ns=174,sequence=5),
                dict(kind='FocusIn',widget='target',monotonic_ns=175,sequence=6)])
        binding=dict(token=row['token'],pid=row['app_pid'],target_id=42,freeze_sha256=frozen)
        values=[dict(binding,schema='issue5260-a09-focus-pipe-v1',kind=e['kind'],widget=e['widget'],
            focus_get='target' if e['kind']=='FocusIn' and e['widget']=='target' else 'other',
            sequence=e['sequence'],event_ns=e['monotonic_ns'],written_ns=e['monotonic_ns']+1) for e in focuses]
        publications=[]
        for value in values:
            blob=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
            publications.append({'value':copy.deepcopy(value),'trace':dict(frame_utf8=blob.decode(),
                sha256=hashlib.sha256(blob).hexdigest(),requested_bytes=len(blob),written_bytes=len(blob),
                started_ns=value['event_ns']+2,completed_ns=value['event_ns']+3,write_error=None)})
        def read(status,start,end,vals=()):
            blob=b''.join((json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode() for v in vals)
            return dict(status=status,started_ns=start,completed_ns=end,hex=blob.hex(),bytes=len(blob),
                sha256=hashlib.sha256(blob).hexdigest())
        reads=[read('DATA',82,85,values[:2]),read('EAGAIN',94,95)]
        frames=[dict(value=copy.deepcopy(v),seen_ns=85) for v in values[:2]]
        if plan['mode']!='STABLE':
            reads.extend([read('DATA',117,140,values[2:4]),read('EAGAIN',141,142)])
            frames.extend(dict(value=copy.deepcopy(v),seen_ns=140) for v in values[2:4])
        if plan['mode']=='DRIFT_RECOVER':
            reads.extend([read('DATA',174,177,values[4:]),read('EAGAIN',177,178)])
            frames.extend(dict(value=copy.deepcopy(v),seen_ns=177) for v in values[4:])
        reads.append(read('EOF',310,311))
        row['pipe']=dict(identity={'read_fd':3,'write_fd':4,'read_inode':99,'write_inode':99,'pipe_buf':4096},
            reads=reads,frames=frames,eof=True,closes=[dict(name='write_fd',fd=4,started_ns=2,completed_ns=3),
                dict(name='read_fd',fd=3,started_ns=312,completed_ns=313)])
        def gate_state(gate,value,seen):
            gate.update(ack=copy.deepcopy(value),state=copy.deepcopy(value))
            gate['samples'][0].update(state=copy.deepcopy(value),seen_ns=seen)
        gate_state(inj['gate'],values[1],85)
        if plan['mode']!='STABLE':
            drift=phase['prior']['drift'];drift['frames']=copy.deepcopy(values[2:4])
            drift['samples'][0]['frames']=copy.deepcopy(values[2:4])
        if plan['mode']=='DRIFT_RECOVER':gate_state(phase['recovery']['gate'],values[-1],177)
        if plan['mode']=='STABLE':
            phase.update(recovery=None,prior_emissions={'keys':3,'saves':1},
                prior={'intervention':None,'drift':None,'dispatch_started_ns':101,'dispatch_completed_ns':195,
                    'dispatch':{'status':'EMITTED','reason':'STABLE'}})
        elif plan['mode']=='DRIFT_REFUSE':
            phase.update(recovery=None,prior_emissions={'keys':0,'saves':0},total_emissions={'keys':0,'saves':0})
            inj.update(key_requests=[],save_requests=[])
        for key,char in zip(inj['key_requests'],plan['payload']):key['char']=char
        mapped=[dict(kind='Map',monotonic_ns=2),dict(kind='Configure',monotonic_ns=3),copy.deepcopy(focuses[0])]
        key_events=[dict(kind='KeyPress',widget='target',char=k['char'],monotonic_ns=k['sync_returned_ns'])
            for k in inj['key_requests']]
        events=copy.deepcopy(mapped)+copy.deepcopy(focuses[1:])+key_events
        if key_events:events.append(dict(kind='Save',widget='target',monotonic_ns=192))
        (directory/'baseline.xwd').write_bytes(b'synthetic-baseline-not-pixels')
        baseline=dict(path='baseline.xwd',exit=0,started_ns=10,completed_ns=20,
            sha256=digest(directory/'baseline.xwd'),bytes=28)
        baseline['bytes']=(directory/'baseline.xwd').stat().st_size
        witness={'scheduled':1,'focus_callbacks':1,'finalizations':1}
        ready=dict(geometry=g,pid=row['app_pid'],token=row['token'],map_configure_events=mapped,
            baseline_frame=baseline,ready_ns=30,readiness=witness)
        row['ready']=ready;cache=f'/tmp/5260-a08-cache-synthetic_{index}'
        first_target=focuses[1]
        focus_ack=dict(token=row['token'],pid=row['app_pid'],target_id=42,widget='target',sequence=2,
            event_ns=80,written_ns=81,schema='issue5260-a07-focus-ack-v1',focus_get='target')
        app.update(schema='issue5260-tk-app-v1',token=row['token'],pid=row['app_pid'],payload=plan['payload'],
            instrumentation_mode='MEMORY_ONLY',events=events,xdg_cache_home=cache,ready_snapshot=copy.deepcopy(ready),
            geometry=g,baseline_frame=baseline,ready_ns=30,readiness=witness,task_file=None,task_file_error=None,
            focus_trace={'mode':'MEMORY_ONLY','events':copy.deepcopy(focuses),'publications':[],
                'callbacks':[dict(event_sequence=e['sequence'],started_ns=e['monotonic_ns'],
                    completed_record_ns=e['monotonic_ns']+1) for e in focuses],
                'ack':focus_ack,'last_state':dict(token=row['token'],pid=row['app_pid'],target_id=42,
                    widget=focuses[-1]['widget'],sequence=focuses[-1]['sequence'],event_ns=focuses[-1]['monotonic_ns'])},
            focus_pipe={'identity':dict(fd=4,inode=99,pipe_buf=4096,nonblocking=True),
                'first_error':None,'publications':publications,'close':dict(fd=4,started_ns=301,completed_ns=302)})
        if key_events:
            app.update(saved_text=plan['payload'],final_target=plan['payload'])
            blob=(json.dumps(dict(schema='issue5260-a12-task-file-v1',token=row['token'],pid=row['app_pid'],
                text=plan['payload']),sort_keys=True,separators=(',',':'))+'\n').encode()
            (directory/'task_result.json').write_bytes(blob)
            app['task_file']=dict(path='task_result.json',started_ns=193,fsynced_ns=194,completed_ns=195,
                sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob))
            (directory/'first_visual.xwd').write_bytes(b'synthetic-first-not-pixels')
            app['first_visual']=dict(schema='issue5260-first-visual-v1',widget='target',observed_ns=189,
                frame=dict(path='first_visual.xwd',exit=0,started_ns=186,completed_ns=187,
                    sha256=digest(directory/'first_visual.xwd'),bytes=(directory/'first_visual.xwd').stat().st_size))
            dump(directory/'first_visual.json',app['first_visual'])
        else:
            app.update(saved_text=None,save_count=0,final_target='',final_decoy='')
            for key in ('first_key_ns','first_key_widget'):app.pop(key,None)
        row.update(app_stdout=json.dumps(app),app_exit=0,app_stderr='',app_start_ns=1,app_end_ns=303,
            worker={'pid':None,'exit':None},cache=dict(token=row['token'],path=cache,created_ns=1,mode=0o700,
                uid=65534,removed=True,cleanup_started_ns=304,cleanup_finished_ns=305))
        dump(directory/'app_result.json',app);dump(directory/'ready.json',ready);rows.append(row)
    raw=dict(schema=fixture['schema'],allocation=fixture['allocation'],fixture=fixture,schedule=expected_rows(fixture),
        rows=rows,fixture_sha256=digest(source/'fixture.json'),freeze_sha256=frozen,source_sha256=freeze['sha256'],
        environment={'image_id':'synthetic-image','display':':97','tk':8.6,'container_id':'synthetic',
            'python':'3.13.5 synthetic','private_exit':{'openbox':0,'xvfb':0},
            'keymap':{'set':{'exit':0},'query':{'exit':0,'stdout':'layout: us'}}})
    path=data/'candidate_stdout.json';dump(path,raw);(data/'candidate_exit.txt').write_text('0\n')
    return path,data,source,raw

class PacketTests(unittest.TestCase):
    def test_six_cell_file_recovery_packet_qualifies(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp));result=inspect(path,data,source)
            self.assertEqual(result['errors'],[],result)
            self.assertEqual(result['hypothesis'],'H_PASS_FINITE_FIXTURE_ONLY')

    def test_omitted_executed_source_cannot_be_hidden_by_rehashing(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp))
            freeze=json.loads((source/'FREEZE.json').read_bytes());freeze['sha256'].pop('app.py')
            dump(source/'FREEZE.json',freeze);raw['source_sha256']=freeze['sha256']
            raw['freeze_sha256']=digest(source/'FREEZE.json');dump(path,raw)
            self.assertIn('source_manifest_coverage',inspect(path,data,source)['errors'])

    def test_coherent_wrong_window_dimensions_are_not_planned_task(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp));row=raw['rows'][0];app=row['app']
            for geometry in [row['ready']['geometry'],app['geometry'],app['ready_snapshot']['geometry']]:
                geometry['root_width']=777
            row['app_stdout']=json.dumps(app);directory=data/'row-000'
            dump(directory/'app_result.json',app);dump(directory/'ready.json',row['ready']);dump(path,raw)
            self.assertTrue(any('task_geometry_dimensions' in e for e in inspect(path,data,source)['errors']))

    def test_coherent_wrong_task_effect_is_h_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp))
            row=next(r for r in raw['rows'] if r['mode']=='STABLE');app=row['app']
            directory=data/f"row-{row['index']:03d}"
            next(e for e in app['events'] if e['kind']=='KeyPress')['widget']='decoy'
            app.update(saved_text=row['payload'][1:],final_target=row['payload'][1:],
                final_decoy=row['payload'][0],first_key_widget='decoy')
            app['first_visual']['widget']='decoy';dump(directory/'first_visual.json',app['first_visual'])
            value=json.loads((directory/'task_result.json').read_bytes());value['text']=app['saved_text']
            dump(directory/'task_result.json',value)
            app['task_file'].update(sha256=digest(directory/'task_result.json'),bytes=(directory/'task_result.json').stat().st_size)
            row['app_stdout']=json.dumps(app);dump(directory/'app_result.json',app);dump(path,raw)
            result=inspect(path,data,source)
            self.assertEqual(result['errors'],[],result)
            self.assertEqual(result['hypothesis'],'H_FAIL_FINITE_FIXTURE_ONLY')
            self.assertTrue(result['task_errors'])

    def test_packet_corruptions_cannot_be_candidate_success(self):
        mutations=[lambda r,d,s:r['rows'][0].update(app_pid=True),
            lambda r,d,s:r['rows'][0].update(app_stdout='{}'),
            lambda r,d,s:r['rows'][0]['pipe']['reads'][0].update(hex='00'),
            lambda r,d,s:r['rows'][0]['injection']['gate']['samples'].clear(),
            lambda r,d,s:(d/'row-000'/'baseline.xwd').write_bytes(b'changed'),
            lambda r,d,s:(d/'row-000'/'app_result.json').write_bytes(b'{}'),
            lambda r,d,s:r['rows'].pop(),
            lambda r,d,s:r['environment'].update(image_id='different'),
            lambda r,d,s:r['rows'][1].update(cache=copy.deepcopy(r['rows'][0]['cache'])),
            lambda r,d,s:next(x for x in r['rows'] if x['mode']=='DRIFT_RECOVER')['injection']['post_admission']['recovery']['gate']['samples'].clear()]
        for i,mutate in enumerate(mutations):
            with self.subTest(i=i),tempfile.TemporaryDirectory() as temp:
                path,data,source,raw=packet(Path(temp));mutate(raw,data,source);dump(path,raw)
                result=inspect(path,data,source)
                self.assertEqual(result['status'],'STOP_AUDIT',result)
                self.assertEqual(result['hypothesis'],'UNQUALIFIED',result)

if __name__=='__main__':unittest.main()
