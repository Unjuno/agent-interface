import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from runtime.integration_checks.workload import reported_dispatch,summarize

class WorkloadTests(unittest.TestCase):
    def reply(self,status='completed',summary=False):
        v={'schema':'agent-interface/review-v1','outcome_summary':{'execution_status':status,'input_release_verified':True},
           'receipt':{'schema':'agent-interface/receipt-view-v3-report-ref','source':{'raw_report':{'result':{'status':status}}}}}
        if summary:v['receipt']={'schema':'agent-interface/receipt-view-dispatch-summary-v1'}
        return {'status':'returned','result':{'content':[{'type':'text','text':json.dumps(v)}]}}

    def test_refused_failed_unknown_and_completed_are_not_transport_success(self):
        for status in ['completed','refused','execution_failed']:
            self.assertEqual(reported_dispatch(self.reply(status))['classification'],'reported_'+status)
        self.assertEqual(reported_dispatch(self.reply(summary=True))['classification'],'reported_completed')
        self.assertEqual(reported_dispatch({'status':'returned','result':{}})['classification'],'unclassified')
        self.assertEqual(reported_dispatch({'status':'refused','dispatched':False})['classification'],'relay_refused_before_dispatch')
        self.assertEqual(reported_dispatch({'status':'unknown_requires_reconciliation'})['classification'],'unknown_requires_reconciliation')

    def test_malformed_conflicting_or_unrecognized_views_stay_unclassified(self):
        for text in ['not json','null','[]',json.dumps({'schema':'other'}),json.dumps({'schema':'agent-interface/review-v1','outcome_summary':{'execution_status':'completed'},'receipt':{'schema':'agent-interface/receipt-view-v3-report-ref','source':{'raw_report':{'result':{'status':'refused'}}}}})]:
            with self.subTest(text=text):
                self.assertEqual(reported_dispatch({'status':'returned','result':{'content':[{'type':'text','text':text}]}})['classification'],'unclassified')
        self.assertEqual(reported_dispatch(self.reply('refused',summary=True))['classification'],'unclassified')

    def test_inspection_error_does_not_erase_completed_input_or_release_failure(self):
        reply=self.reply();view=json.loads(reply['result']['content'][0]['text'])
        view['post_dispatch_inspection']={'error':'foreign family'}
        view['outcome_summary']['input_release_verified']=False
        reply['result']['content'][0]['text']=json.dumps(view)
        row=reported_dispatch(reply)
        self.assertEqual(row,{'classification':'reported_completed','input_release_verified':False,'inspection':'error'})

    def test_real_timeline_counts_refusal_and_partial_without_modifying_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);reply={'status':'refused','dispatched':False,'next_id':1,'error':'unknown relay tool'}
            (root/'reply-1.json').write_text(json.dumps(reply))
            (root/'request-1.json').write_text(json.dumps({'id':1,'tool':'interface_dispatch'}))
            digest=hashlib.sha256((root/'reply-1.json').read_bytes()).hexdigest()
            events=[]
            for kind,stamp,attempt in [('send_requested',1,1),('reply_available',2,1),('send_requested',3,2),('transport_closed',4,None)]:
                row={'schema':'agent-interface/relay-host-event-v1','sequence':len(events)+1,'kind':kind,'host_monotonic_ms':stamp}
                if attempt:row.update(attempt=attempt,tool='interface_dispatch',relay_id=None,reply_sha256=digest)
                events.append(row)
            (root/'host-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
            before={p.name:p.read_bytes() for p in root.iterdir()}
            result=summarize(root)
            self.assertEqual(result['timeline_status'],'partial')
            self.assertEqual(result['dispatch_receipts'],{'no_reply_outcome_unknown':1,'relay_refused_before_dispatch':1})
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir()})
            self.assertIsNone(result['time_partition'])

    def test_changed_reply_after_validation_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'reply-1.json').write_text('{}')
            timing={'calls':[{'attempt':1,'tool':'interface_dispatch','reply_ms':1,'presentations':[],'reviews':[]}],
                    'input_sha256':{'reply-1.json':'wrong'}}
            with patch('runtime.integration_checks.workload.summarize_timing',return_value=timing):
                with self.assertRaisesRegex(ValueError,'reply changed'):summarize(td)

if __name__=='__main__':unittest.main()
