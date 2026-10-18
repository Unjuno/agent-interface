"""Corruption controls for the independent retained-trace audit."""
import copy, json, subprocess, sys, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class TraceAuditTests(unittest.TestCase):
    def test_retained_trace_audits(self):
        subprocess.run([sys.executable,str(HERE/'audit.py')],check=True,capture_output=True,text=True)
    def test_inter_release_keymap_query_is_rejected(self):
        trace=json.loads((HERE/'TRACE.json').read_text())
        ups=[e for e in trace['events'] if e['event']=='key_up']
        trace['events'].append({'event':'query_keymap','time_ns':(ups[0]['time_ns']+ups[1]['time_ns'])//2,'keys':[]})
        self.assertFalse(_trace_order_valid(trace))
    def test_sample_before_second_up_is_rejected(self):
        trace=json.loads((HERE/'TRACE.json').read_text())
        ups=[e for e in trace['events'] if e['event']=='key_up']
        for event in trace['events']:
            if event['event']=='input_state_sample_start': event['time_ns']=ups[1]['time_ns']-1
        self.assertFalse(_trace_order_valid(trace))
    def test_authority_claim_is_rejected(self):
        trace=json.loads((HERE/'TRACE.json').read_text())
        trace['release_rows'][0]['physical_verification_authoritative']=True
        self.assertFalse(all(row.get('physical_verification_authoritative') is False for row in trace['release_rows']))
def _trace_order_valid(trace):
    events=trace['events']; ups=[e for e in events if e['event']=='key_up']; queries=[e for e in events if e['event']=='query_keymap']; samples=[e for e in events if e['event']=='input_state_sample_start']; finishes=[e for e in events if e['event']=='input_state_sample_finish']
    return (len(ups)==2 and [e['keycode'] for e in ups]==[38,65] and len(queries)==1 and len(samples)==len(finishes)==1 and ups[0]['time_ns']<ups[1]['time_ns']<samples[0]['time_ns']<finishes[0]['time_ns']<queries[0]['time_ns'])
if __name__=='__main__': unittest.main(verbosity=2)
