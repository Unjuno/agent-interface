import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit import focus_trace_errors


class FocusTraceAuditTests(unittest.TestCase):
    def setUp(self):
        self.events=[{'kind':'FocusIn','widget':'decoy','monotonic_ns':100,'sequence':1},
                     {'kind':'FocusIn','widget':'target','monotonic_ns':200,'sequence':2}]
        self.state={'token':'fresh','pid':17,'target_id':42,'widget':'target','sequence':2,'event_ns':200}
        self.ack={**self.state,'schema':'issue5260-a07-focus-ack-v1','focus_get':'target','written_ns':201}
        self.row={'instrumentation_mode':'MEMORY_ONLY','token':'fresh','app_pid':17,
            'ready':{'geometry':{'target_id':42}},
            'app':{'events':self.events,'focus_trace':{'mode':'MEMORY_ONLY',
                   'events':self.events,'publications':[],'last_state':self.state,'ack':self.ack}}}
        self.row['app']['focus_trace']['callbacks']=[{'event_sequence':1,'started_ns':100,'completed_record_ns':101},
                                                    {'event_sequence':2,'started_ns':200,'completed_record_ns':202}]

    def test_valid_memory_trace_without_files(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(focus_trace_errors(Path(directory),self.row),[])

    def test_memory_cannot_claim_file_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            row=copy.deepcopy(self.row)
            row['app']['focus_trace']['publications']=[{'path':'focus_state.json'}]
            self.assertTrue(focus_trace_errors(Path(directory),row))
            (Path(directory)/'focus_state.json').write_text('{}')
            self.assertTrue(focus_trace_errors(Path(directory),self.row))

    def test_snapshot_sequence_and_identity_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for mutate in (lambda r:r['app']['focus_trace']['last_state'].update(pid=99),
                           lambda r:r['app']['focus_trace']['ack'].update(sequence=True),
                           lambda r:r['app']['focus_trace'].update(mode='unknown')):
                row=copy.deepcopy(self.row);mutate(row)
                self.assertTrue(focus_trace_errors(Path(directory),row))

    def test_file_mode_missing_publication_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            row=copy.deepcopy(self.row);row['instrumentation_mode']='SYNC_FILE'
            row['app']['focus_trace']['mode']='SYNC_FILE'
            self.assertTrue(focus_trace_errors(Path(directory),row))

    def sync_row(self,root):
        row=copy.deepcopy(self.row);row['instrumentation_mode']='SYNC_FILE'
        trace=row['app']['focus_trace'];trace['mode']='SYNC_FILE'
        trace['callbacks'][0]['completed_record_ns']=116
        trace['callbacks'][1]['completed_record_ns']=226
        values=[('focus_state.json',1,{**self.state,'widget':'decoy','sequence':1,'event_ns':100}),
                ('focus_state.json',2,self.state),('focus_ack.json',2,self.ack)]
        for name,sequence,value in values:
            start=110 if sequence==1 else (210 if name=='focus_state.json' else 220)
            blob=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
            writer={'path':name,'started_ns':start+1,'flushed_ns':start+2,'fsynced_ns':start+3,
                'replace_started_ns':start+4,'replace_finished_ns':start+5,
                'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob)}
            trace['publications'].append({'path':name,'event_sequence':sequence,
                'started_ns':start,'completed_ns':start+6,'writer_trace':writer})
            (root/name).write_bytes(blob)
        return row

    def test_valid_sync_file_trace_and_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.assertEqual(focus_trace_errors(root,self.sync_row(root)),[])

    def test_hash_clock_bool_and_file_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for mutate in (lambda r:r['app']['focus_trace']['publications'][0]['writer_trace'].update(sha256='0'*64),
                           lambda r:r['app']['focus_trace']['publications'][0].update(event_sequence=True),
                           lambda r:r['app']['focus_trace']['publications'][1].update(started_ns=50)):
                row=self.sync_row(root);mutate(row)
                self.assertTrue(focus_trace_errors(root,row))
            row=self.sync_row(root);(root/'focus_ack.json').write_text('{}')
            self.assertTrue(focus_trace_errors(root,row))


if __name__=='__main__':unittest.main()
