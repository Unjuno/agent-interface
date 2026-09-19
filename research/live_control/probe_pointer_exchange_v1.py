"""Recorded-reply controls and live-cohort audit. Controls perform no GUI input."""
import copy,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from pointer_exchange_v1 import run
from PIL import Image
from session_v4 import Decoder

HERE=Path(__file__).resolve().parent
ROOT=HERE/'results/pointer-caller-01'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    original=read(ROOT/'move-call/report.json');source=read(ROOT/'move-call/source-batch.json')
    # Remap only synthetic control images to the copied archive; raw replies stay intact.
    for record in source['records']:
        if record.get('event')=='observation':record['image']=str(ROOT/Path(record['image']).name)
    rows={}
    for case in ('valid','wrong_clock_echo','interleaved_clock','advanced_sequence','clock_gap',
                 'clock_timeout','bad_cursor','wrong_terminal','program_rejected','transport_error'):
        calls=[]
        def query(request):
            calls.append(request)
            if case=='transport_error':raise TimeoutError('injected uncertain exchange')
            reply=copy.deepcopy(original['exchanges'][len(calls)-1]['reply'])
            for record in reply['records']:
                if record.get('event')=='command':record['command']['transport_request_id']=request['request_id']
                if record.get('event')=='observation':record['image']=str(ROOT/Path(record['image']).name)
            reply['cursor']=request['after']+len(reply['records'])
            if len(calls)==1:
                if case=='wrong_clock_echo':reply['records'][0]['command']['transport_request_id']='other'
                elif case=='interleaved_clock':
                    reply['records'].insert(1,{'event':'command','command':{'op':'clock','transport_request_id':'other'}});reply['cursor']+=1
                elif case=='advanced_sequence':reply['records'][-1]['sequence']+=1
                elif case=='clock_gap':reply['status']='gap'
                elif case=='clock_timeout':reply['status']='timeout'
                elif case=='bad_cursor':reply['cursor']+=1
            else:
                if case=='wrong_terminal':reply['records'][-1]['id']='other'
                elif case=='program_rejected':reply['status']='unattributed_rejection'
            return reply
        result=run(query,source,ROOT,'move-save',read(ROOT/'move-steps.json'),30000,lambda *args:None)
        assert len(calls)==(2 if case in ('valid','wrong_terminal','program_rejected') else 1)
        assert result['state']==('terminal' if case=='valid' else 'needs_reconciliation'),(case,result)
        if case!='valid':assert 'continuation_batch' not in result
        rows[case]={'state':result['state'],'queries':len(calls),'reason':result.get('reason')}
    events=[json.loads(line) for line in (ROOT/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');count=0
    for record in events:
        if record['event']!='observation':continue
        count+=1;assert record['sequence']==count
        frame=decoder.accept((ROOT/f'{count:03d}.ait').read_bytes())
        with Image.open(ROOT/Path(record['image']).name) as im:assert im.tobytes()==frame.pixels and im.size==(frame.width,frame.height)
    final=read(ROOT/'finish.json')['records'][-1]
    assert final['success'] is True
    rectangle=ET.parse(ROOT/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    assert all(rectangle.get(k)==v for k,v in final['actual'].items())
    assert all(r['status']=='completed' and r['release']['verified'] for r in events if r['event']=='terminal')
    # Complete transport stream prefix in the recorded exchanges, with no omission.
    batches=[read(ROOT/'batch.json')]
    for name in ('call','move-call'):
        batches += [r['reply'] for r in read(ROOT/name/'report.json')['exchanges']]
    batches.append(read(ROOT/'finish.json'))
    full=[];cursor=0
    for batch in batches:
        assert batch['cursor']==cursor+len(batch['records']);cursor=batch['cursor'];full+=batch['records']
    assert full==events
    result={'controls':rows,'exact_frames':count,'full_prefix_records':len(full),
            'task_success':True,'scope':'one live Inkscape readiness plus mocked controls; no cross-domain qualification',
            'source_hashes_post_run':{n:sha(HERE/n) for n in ('pointer_exchange_v1.py','pointer_socket_entry_v1.py','probe_pointer_exchange_v1.py')},
            'source_provenance':'new caller/adapter hashes captured after run; domain manifest remains archived',
            'automatic_input_retries':0}
    (ROOT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
