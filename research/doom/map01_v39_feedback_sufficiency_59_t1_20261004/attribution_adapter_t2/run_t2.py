"""Produce a bounded source-composition result for the V15 attribution adapter."""
from __future__ import annotations
import json
import argparse
from pathlib import Path
from adapter import adapt_session_records
from map01_scorer_stdio_adapter_v1 import ScorerFileSink
from independent_progress_clock_v2 import ProgressSample
ROOT=Path(__file__).resolve().parent

def down(token='intent-a',identifier='plan-a',step=0,key='space',owner='owner-1',admitted=80):
    return {'event':'input_admission','key':key,'admitted_ns':admitted,'input_ack_ns':admitted+5,
            'valid_until_ns':900,'id':identifier,'step':step,'owner_id':owner,'intent_token':token}

def up(token='intent-a',identifier='plan-a',step=0,key='space',owner='owner-1',verified=True,sync_ns=320,batch_id=None,size=1,position=0):
    receipt={'event':'owner_explicit_keyup','operation':'up','key':key,'owner_id':owner,
             'intent_token':token,'valid_until_ns':900,'owner_keyrelease_started_ns':310,
             'owner_sync_returned_ns':sync_ns,'cancel_requested_after_sync':False,
             'server_sync_completed':True,'physical_verification_authoritative':False}
    return {'event':'input_release_transition','operation':'up','key':key,'owner_id':owner,
            'intent_token':token,'id':identifier,'step':step,'release_call_started_ns':305,
            'release_call_returned_ns':330,'owner_thread_keyup_receipt':receipt,
            'owner_thread_keyup_verified':verified,'owner_thread_keyup_receipt_count':1,
            'owner_thread_keyup_history_complete':True,'owner_thread_keyup_verified_after_batch':verified,
            'owner_transition_verified':verified,'release_batch_schema':'input-release-batch-v3',
            'release_batch_identifier':batch_id or 'batch-'+identifier,'release_batch_step':step,
            'release_batch_size':size,'release_batch_position':position,'release_batch_complete':True,
            'physical_verification_authoritative':False}

def build_scorer_stream(run_dir):
    sink=ScorerFileSink(run_dir/'scorer')
    values=[ProgressSample(100,0,0,False,False,False),ProgressSample(300,1,0,False,False,False)]
    for i,sample in enumerate(values):
        sink({'scheduled_ns':sample.sample_ns,'sample_started_ns':sample.sample_ns,
              'sample_finished_ns':sample.sample_ns,'start_lateness_ns':0,
              'missed_periods_before':0,'payload':sample})
    summary=sink.finalize({'owner_thread_id':1,'samples':2,'commands':0,
                           'missed_sample_periods':0,'eof':True,'sample_hz':35.0})
    samples=[json.loads(x) for x in (run_dir/'scorer/scorer-samples.jsonl').read_text().splitlines() if x]
    events=[json.loads(x) for x in (run_dir/'scorer/scorer-events.jsonl').read_text().splitlines() if x]
    return samples,events,summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,default=ROOT/'run/replay',
                        help='new, empty directory for this replay (default: run/replay)')
    args=parser.parse_args()
    run_dir=args.run_dir
    try:
        run_dir.mkdir(parents=True,exist_ok=False)
    except FileExistsError as exc:
        raise SystemExit(f'refusing to append or overwrite existing run directory: {run_dir}') from exc
    samples,events,summary=build_scorer_stream(run_dir)
    inputs={
      'single_verified':[down(),up()],
      'overlapping':[down(),up(),down('intent-b','cover-b',key='a'),up('intent-b','cover-b',key='a')],
      'mismatched_release':[down(),up('intent-other','plan-other')],
      'unverified_release':[down(),up(verified=False)],
      'incomplete_release_batch':[down(),up(size=2)],
      'unbound_admission':[dict(down(),intent_token=None),up()],
    }
    (run_dir/'input-records.json').write_text(json.dumps(inputs,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    expected_names=list(inputs)
    cases={name:adapt_session_records(samples,events,rows) for name,rows in inputs.items()}
    result={'schema':'v15-attribution-adapter-t2-result-v1','scope':'synthetic producer-composition construction only',
            'scorer_sink_summary':summary,'scenarios':cases,'scenario_names':expected_names}
    (run_dir/'candidate.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
