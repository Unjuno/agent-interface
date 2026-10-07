"""Filesystem packet construction only: never launches a GUI or candidate."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit import inspect
from synthetic_a09_packet import packet as old_packet
from synthetic_a08_packet import dump,digest


def packet(root):
    path,data,source,raw=old_packet(root)
    raw['fixture']['drift_timeout_ms']=500
    dump(source/'fixture.json',raw['fixture'])
    freeze=json.loads((source/'FREEZE.json').read_bytes())
    freeze['sha256']['fixture.json']=digest(source/'fixture.json')
    dump(source/'FREEZE.json',freeze)
    frozen=digest(source/'FREEZE.json')
    raw.update(fixture_sha256=digest(source/'fixture.json'),freeze_sha256=frozen,
               source_sha256=freeze['sha256'])
    empty=hashlib.sha256(b'').hexdigest()
    for row in raw['rows']:
        app=row['app'];inj=row['injection'];trace=app['focus_trace']
        directory=data/f"row-{row['index']:03d}"
        row['ready']['geometry'].update(decoy_root_x=10,decoy_root_y=0,
            decoy_width=100,decoy_height=20)
        app['geometry']=copy.deepcopy(row['ready']['geometry'])
        app['ready_snapshot']=copy.deepcopy(row['ready'])
        drift=row['mode']!='STABLE'
        if drift:
            extra=[dict(kind='FocusOut',widget='target',sequence=3,monotonic_ns=188),
                   dict(kind='FocusIn',widget='decoy',sequence=4,monotonic_ns=192)]
            trace['events'].extend(copy.deepcopy(extra))
            trace['callbacks'].extend(dict(event_sequence=e['sequence'],
                started_ns=e['monotonic_ns'],completed_record_ns=e['monotonic_ns']+1)
                for e in extra)
            trace['last_state'].update(widget='decoy',sequence=4,event_ns=192)
            app['events'][4:4]=copy.deepcopy(extra)
        if row['mode']=='DRIFT_STALE_CONTROL':
            for event in app['events']:
                if event['kind']=='KeyPress':event['widget']='decoy'
            app.update(first_key_widget='decoy',saved_text='',final_target='',final_decoy='hxy')
            app['first_visual']['widget']='decoy'
        if row['mode']=='DRIFT_REFUSE':
            inj.update(key_requests=[],save_requests=[])
            app['events']=[e for e in app['events'] if e['kind'] not in ('KeyPress','Save')]
            for name in ('first_visual','first_key_widget','first_key_ns'):app.pop(name)
            app.update(save_count=0,saved_text=None,final_target='',final_decoy='')
            (directory/'first_visual.json').unlink()
            (directory/'first_visual.xwd').unlink()
        publications=[];frames=[];reads=[]
        for event in trace['events']:
            value=dict(token=row['token'],pid=row['app_pid'],target_id=11,
                freeze_sha256=frozen,schema='issue5260-a09-focus-pipe-v1',
                kind=event['kind'],widget=event['widget'],
                focus_get='target' if event['widget']=='target' and event['kind']=='FocusIn' else 'other',
                sequence=event['sequence'],event_ns=event['monotonic_ns'],
                written_ns=event['monotonic_ns']+1)
            blob=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
            end=event['monotonic_ns']+5
            reads.append(dict(status='DATA',started_ns=end-1,completed_ns=end,
                hex=blob.hex(),bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()))
            frames.append(dict(value=copy.deepcopy(value),seen_ns=end))
            publications.append(dict(value=value,trace=dict(started_ns=event['monotonic_ns']+2,
                completed_ns=event['monotonic_ns']+3,frame_utf8=blob.decode(),
                sha256=hashlib.sha256(blob).hexdigest(),requested_bytes=len(blob),
                written_bytes=len(blob),write_error=None)))
        reads.insert(2,dict(status='EAGAIN',started_ns=176,completed_ns=177,
                            hex='',bytes=0,sha256=empty))
        if drift:reads.append(dict(status='EAGAIN',started_ns=198,completed_ns=199,
                                  hex='',bytes=0,sha256=empty))
        reads.append(dict(status='EOF',started_ns=app['ended_ns']+1,
            completed_ns=app['ended_ns']+2,hex='',bytes=0,sha256=empty))
        app['focus_pipe']['publications']=publications
        row['pipe'].update(reads=reads,frames=frames)
        state=copy.deepcopy(frames[1]['value'])
        inj['gate']=dict(status='ADMITTED',ack=copy.deepcopy(state),state=state,
            started_ns=160,decided_ns=180,deadline_ns=500000160,
            reason='CURRENT_TARGET_RECEIPT',samples=[dict(checked_ns=180,
                state=copy.deepcopy(state),seen_ns=175,errors=[],read_attempts=3)])
        observed=None;intervention=None
        if drift:
            values=[copy.deepcopy(f['value']) for f in frames[2:]]
            intervention=dict(widget='decoy',x=60,y=10,started_ns=181,completed_ns=182)
            observed=dict(started_ns=183,decided_ns=200,deadline_ns=500000183,
                status='OBSERVED_DRIFT',reason='BOUND_TARGET_OUT_DECOY_IN',frames=values,
                samples=[dict(checked_ns=200,read_attempts=6,frames=copy.deepcopy(values),errors=[])])
            # Dispatch begins after observation, before the first key request.
            for key in inj['key_requests']:
                key['request_started_ns']+=10;key['sync_returned_ns']+=10
            for event in app['events']:
                if event['kind']=='KeyPress':event['monotonic_ns']+=10
            if inj['key_requests']:
                app['first_key_ns']+=10
                app['first_visual']['frame']['started_ns']+=10
                app['first_visual']['frame']['completed_ns']+=10
                app['first_visual']['observed_ns']+=10
                inj['save_requests'][0]['request_started_ns']+=10
                inj['save_requests'][0]['sync_returned_ns']+=10
                for event in app['events']:
                    if event['kind']=='Save':event['monotonic_ns']+=10
        refuse=row['mode']=='DRIFT_REFUSE'
        inj['post_admission']=dict(intervention=intervention,drift=observed,
            dispatch_started_ns=201 if drift else 181,
            dispatch_completed_ns=inj['save_requests'][0]['sync_returned_ns'] if not refuse else 202,
            dispatch=dict(status='REFUSED' if refuse else 'EMITTED',
                          reason='OBSERVED_DRIFT' if refuse else row['mode']))
        row['app_stdout']=json.dumps(app)
        dump(directory/'app_result.json',app);dump(directory/'ready.json',row['ready'])
        if not refuse:dump(directory/'first_visual.json',app['first_visual'])
    dump(path,raw)
    return path,data,source,raw


class PacketTests(unittest.TestCase):
    def test_non_object_packet_is_recorded_as_unqualified(self):
        for value in (None,[],17):
            with self.subTest(value=value),tempfile.TemporaryDirectory() as temp:
                path,data,source,raw=packet(Path(temp));dump(path,value)
                result=inspect(path,data,source)
                self.assertEqual(result['status'],'STOP_AUDIT')
                self.assertEqual(result['hypothesis'],'UNQUALIFIED')

    def test_non_object_row_is_recorded_as_unqualified(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp));raw['rows'][0]=None;dump(path,raw)
            self.assertEqual(inspect(path,data,source)['status'],'STOP_AUDIT')

    def test_literal_six_row_packet_qualifies(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp))
            result=inspect(path,data,source)
            self.assertEqual(result['errors'],[],result)
            self.assertEqual(result['hypothesis'],'H_PASS_FINITE_FIXTURE_ONLY')

    def test_missing_drift_poll_rejected_despite_observed_label(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp))
            row=next(r for r in raw['rows'] if r['mode']=='DRIFT_REFUSE')
            row['injection']['post_admission']['drift']['samples']=[]
            dump(path,raw)
            result=inspect(path,data,source)
            self.assertEqual(result['hypothesis'],'UNQUALIFIED')
            self.assertTrue(any('poll_custody' in e for e in result['errors']),result)

    def test_independent_file_and_receipt_corruptions_rejected(self):
        mutations=[
            lambda r,d,s:r.update(freeze_sha256='0'*64),
            lambda r,d,s:r['environment'].update(image_id='wrong'),
            lambda r,d,s:r['rows'].pop(),
            lambda r,d,s:r['rows'][0].update(app_pid=True),
            lambda r,d,s:r['rows'][0].update(app_stdout='{}'),
            lambda r,d,s:r['rows'][0].update(app_stderr='Tk callback error'),
            lambda r,d,s:(d/'row-000'/'ready.json').write_bytes(b'{}'),
            lambda r,d,s:(d/'row-000'/'app_result.json').write_bytes(b'{}'),
            lambda r,d,s:(d/'row-000'/'baseline.xwd').write_bytes(b'changed'),
            lambda r,d,s:r['rows'][1].update(cache=copy.deepcopy(r['rows'][0]['cache'])),
            lambda r,d,s:r['rows'][0]['pipe']['reads'][0].update(hex='00'),
            lambda r,d,s:r['rows'][0]['injection']['gate']['samples'].clear(),
        ]
        for index,mutation in enumerate(mutations):
            with self.subTest(index=index),tempfile.TemporaryDirectory() as temp:
                path,data,source,raw=packet(Path(temp));mutation(raw,data,source);dump(path,raw)
                result=inspect(path,data,source)
                self.assertEqual(result['status'],'STOP_AUDIT',result)
                self.assertEqual(result['hypothesis'],'UNQUALIFIED',result)

if __name__=='__main__':unittest.main()
