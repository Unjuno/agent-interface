"""A09 synthetic complete records; not scientific GUI results."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit import inspect
from synthetic_a08_packet import synthetic_packet,dump,digest


def packet(root):
    path,data,source,raw=synthetic_packet(root)
    fixture=raw['fixture'];fixture.update(ack_timeout_ms=500,ack_poll_ms=1,ack_max_age_ms=50)
    dump(source/'fixture.json',fixture)
    freeze=json.loads((source/'FREEZE.json').read_bytes())
    freeze['sha256']['fixture.json']=digest(source/'fixture.json')
    dump(source/'FREEZE.json',freeze)
    frozen=digest(source/'FREEZE.json')
    raw.update(fixture_sha256=digest(source/'fixture.json'),freeze_sha256=frozen,source_sha256=freeze['sha256'])
    for row in raw['rows']:
        app=row['app'];injection=row['injection'];trace=app['focus_trace']
        directory=data/f"row-{row['index']:03d}"
        if row['mode']=='PIPE_ACK_WRONG_TARGET':
            injection.update(click_widget='decoy',x=60,y=10,key_requests=[],save_requests=[])
            row['ready']['geometry'].update(decoy_root_x=10,decoy_root_y=0,decoy_width=100,decoy_height=20)
            app['geometry']=copy.deepcopy(row['ready']['geometry'])
            app['ready_snapshot']=copy.deepcopy(row['ready'])
            app['events']=copy.deepcopy(row['ready']['map_configure_events'])
            trace.update(events=copy.deepcopy(trace['events'][:1]),callbacks=trace['callbacks'][:1],
                ack=None,last_state={'token':row['token'],'pid':row['app_pid'],'target_id':11,
                                    'widget':'decoy','sequence':1,'event_ns':5})
            for name in ('first_visual','first_key_widget','first_key_ns'):app.pop(name)
            app.update(save_count=0,saved_text=None,final_target='',final_decoy='',ended_ns=600_000_000)
            row.update(app_end_ns=600_000_001)
            row['cache'].update(cleanup_started_ns=600_000_002,cleanup_finished_ns=600_000_003)
            (directory/'first_visual.json').unlink();(directory/'first_visual.xwd').unlink()
        publications=[];frames=[];reads=[]
        for event in trace['events']:
            value={'token':row['token'],'pid':row['app_pid'],'target_id':11,'freeze_sha256':frozen,
                'schema':'issue5260-a09-focus-pipe-v1','kind':event['kind'],'widget':event['widget'],
                'focus_get':'target' if event['widget']=='target' else 'other',
                'sequence':event['sequence'],'event_ns':event['monotonic_ns'],
                'written_ns':event['monotonic_ns']+1}
            blob=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
            end=event['monotonic_ns']+5
            reads.append({'status':'DATA','started_ns':end-1,'completed_ns':end,
                'hex':blob.hex(),'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
            frames.append({'value':copy.deepcopy(value),'seen_ns':end})
            publications.append({'value':value,'trace':{'started_ns':event['monotonic_ns']+2,
                'completed_ns':event['monotonic_ns']+3,'frame_utf8':blob.decode(),
                'sha256':hashlib.sha256(blob).hexdigest(),'requested_bytes':len(blob),
                'written_bytes':len(blob),'write_error':None}})
        reads.append({'status':'EOF','started_ns':app['ended_ns']+1,'completed_ns':app['ended_ns']+2,
            'hex':'','bytes':0,'sha256':hashlib.sha256(b'').hexdigest()})
        app['focus_pipe']={'identity':{'fd':5,'inode':80+row['index'],'nonblocking':True,'pipe_buf':4096},
            'first_error':None,'publications':publications,
            'close':{'fd':5,'started_ns':app['ended_ns']-2,'completed_ns':app['ended_ns']-1}}
        row['pipe']={'identity':{'read_fd':4,'write_fd':5,'read_inode':80+row['index'],
            'write_inode':80+row['index'],'pipe_buf':4096},'reads':reads,'frames':frames,'eof':True,
            'closes':[{'name':'write_fd','fd':5,'started_ns':1,'completed_ns':2},
                      {'name':'read_fd','fd':4,'started_ns':app['ended_ns']+3,'completed_ns':app['ended_ns']+4}]}
        if row['mode']!='NOW_TARGET':
            state=copy.deepcopy(frames[-1]['value'])
            wrong=row['mode']=='PIPE_ACK_WRONG_TARGET';decided=500_000_160 if wrong else 180
            errors=['not_current_target','receipt_clock_order','receipt_expired'] if wrong else []
            injection['gate']={'status':'REFUSED' if wrong else 'ADMITTED','ack':None if wrong else state,
                'state':state,'started_ns':160,'decided_ns':decided,'deadline_ns':500_000_160,
                'reason':'TIMEOUT' if wrong else 'CURRENT_TARGET_RECEIPT',
                'samples':[{'checked_ns':decided,'state':state,'seen_ns':frames[-1]['seen_ns'],
                            'errors':errors,'read_attempts':len(reads)-1}]}
        row['app_stdout']=json.dumps(app)
        dump(directory/'app_result.json',app);dump(directory/'ready.json',row['ready'])
    dump(path,raw)
    return path,data,source,raw


class PacketTests(unittest.TestCase):
    def test_complete_literal_packet_qualifies_finite_hypothesis(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp))
            result=inspect(path,data,source)
            self.assertEqual(result['errors'],[],result)
            self.assertEqual(result['hypothesis'],'H_PASS_FINITE_FIXTURE_ONLY')

    def test_source_environment_and_missing_row_fail(self):
        for mutation in (lambda r:r.update(freeze_sha256='0'*64),
                         lambda r:r['environment'].update(image_id='wrong'),lambda r:r['rows'].pop()):
            with tempfile.TemporaryDirectory() as temp:
                path,data,source,raw=packet(Path(temp));mutation(raw);dump(path,raw)
                self.assertEqual(inspect(path,data,source)['status'],'STOP_AUDIT')

    def test_file_and_app_receipt_corruptions_refused(self):
        mutations=[lambda r,d,s:(d/'row-000'/'ready.json').write_bytes(b'{}'),
            lambda r,d,s:(d/'row-000'/'app_result.json').write_bytes(b'{}'),
            lambda r,d,s:(d/'row-000'/'baseline.xwd').write_bytes(b'changed'),
            lambda r,d,s:r['rows'][0].update(app_stdout='{}'),
            lambda r,d,s:r['rows'][0].update(app_stderr='Tk callback error'),
            lambda r,d,s:r['rows'][0].update(app_pid=True),
            lambda r,d,s:r['rows'][1].update(cache=copy.deepcopy(r['rows'][0]['cache']))]
        for index,mutation in enumerate(mutations):
            with self.subTest(index=index),tempfile.TemporaryDirectory() as temp:
                path,data,source,raw=packet(Path(temp));mutation(raw,data,source);dump(path,raw)
                self.assertEqual(inspect(path,data,source)['status'],'STOP_AUDIT')

    def test_finite_misrouting_is_h_fail_not_method_stop(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp))
            row=next(row for row in raw['rows'] if row['mode']=='PIPE_ACK_TARGET')
            app=row['app'];key=next(event for event in app['events'] if event['kind']=='KeyPress')
            key['widget']='decoy';app.update(first_key_widget='decoy',saved_text='xy',final_target='xy',final_decoy='h')
            app['first_visual']['widget']='decoy'
            row['app_stdout']=json.dumps(app);directory=data/f"row-{row['index']:03d}"
            dump(directory/'app_result.json',app);dump(directory/'first_visual.json',app['first_visual']);dump(path,raw)
            result=inspect(path,data,source)
            self.assertEqual(result['errors'],[],result)
            self.assertEqual(result['hypothesis'],'H_FAIL_FINITE_FIXTURE_ONLY')


if __name__=='__main__':unittest.main()
