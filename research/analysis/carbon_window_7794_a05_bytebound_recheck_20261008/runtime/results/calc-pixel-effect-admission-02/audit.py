import base64,csv,hashlib,io,json
from pathlib import Path

def require(ok,message):
 if not ok:raise ValueError(message)
def load(root):
 root=Path(root);case=root/'live'
 def read(p):return json.loads(p.read_text())
 requests=[read(case/'exchange'/f'request-{i}.json') for i in range(1,13)]
 stream=[json.loads(line) for line in (case/'primary-stream.jsonl').read_text().splitlines()]
 metadata={}
 for i in (1,3,5,7,9,11,12):
  response=read(case/'exchange'/f'original-reply-{i}.json')
  metadata[i]=next(json.loads(x['text']) for x in response['result']['content'] if x['type']=='text')
 inputs={i:read(Path(metadata[i]['call_directory'])/'report.json') for i in (5,7,11)}
 image_records=[image for row in stream for image in row.get('result',{}).get('images',[])]
 images=[(image,Path(image['path']).read_bytes()) for image in image_records]
 return dict(requests=requests,stream=stream,metadata=metadata,inputs=inputs,images=images,
  reading=read(root/'entry-reading/reading.json'),raw_tsv={n:(root/'entry-reading'/f'{n}.tsv').read_text() for n in ('A1','A2','B1_blank_control')},
  cleanup=read(case/'cleanup.json'),effect=read(case/'evaluation.json'))
def check(s):
 q=s['requests'];m=s['metadata']
 require([x['id'] for x in q]==list(range(1,13)),'command identity/order')
 require([x['method'] for x in q]==['observe','review','call','acknowledgeText','call','review','call','review','call','review','call','call'],'command methods')
 require(q[-1]['args']==['interface_close',{}],'explicit close')
 require(len(s['stream'])==14 and s['stream'][0]['status']=='ready' and s['stream'][-1]['status']=='terminal' and s['stream'][-1]['exit']=={'code':0,'signal':None} and all(x['status']=='returned' for x in s['stream'][1:-1]),'stream failure/count')
 require(len(s['images'])==4,'images')
 for image,data in s['images']:
  require(len(data)==image['bytes'] and hashlib.sha256(data).hexdigest()==image['sha256'],'original image identity')
 require(s['reading']['source_sha256']==s['images'][1][0]['sha256'],'reading source')
 literal={'A1':'317','A2':'529','B1_blank_control':'unknown'}
 observed={}
 for name,tsv in s['raw_tsv'].items():
  words=[row for row in csv.DictReader(io.StringIO(tsv),delimiter='\t') if row['level']=='5' and row['text'].strip()]
  observed[name]=words[0]['text'] if len(words)==1 and float(words[0]['conf'])>=90 else 'unknown'
 require(observed==literal,'visible effect/control differs')
 require({x['region']:x['value'] for x in s['reading']['rows']}==observed,'OCR projection')
 require(observed['A1']!='318','wrong expected value accepted')
 for i in (5,7):
  v=s['inputs'][i]['result'];release=v['execution']['releases']
  require(v['status']=='completed' and v['recovery_required'] is False,'prefix incomplete')
  require(bool(release) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in release),'prefix release')
 require(m[9]['status']=='target_reviewed' and m[9]['binding_revision']==2 and m[9]['capture_consistency']=='matched','target review')
 require(m[9]['evidence']['window_id']==8390723 and m[9]['evidence']['family_root']==8389124,'target family')
 p=q[10]['args'][1]
 require(p['current_binding_revision']==2 and p['program']['source']['binding_revision']==2,'stale binding')
 require(s['inputs'][11]['result']['status']=='refused' and s['inputs'][11]['result']['error']=='LEASE_EXPIRED' and 'execution' not in s['inputs'][11]['result'],'refusal erased')
 require(m[11]['post_dispatch_inspection']['input_dispatched'] is False and m[11]['post_dispatch_inspection']['status']=='skipped','refusal input')
 require(m[12]['status']=='closed' and m[12]['release']['verified'] is True and m[12]['release']['keys_down']==[] and m[12]['release']['buttons_down']==[],'close neutrality')
 require(s['cleanup']['host_exit']==0 and len(s['cleanup']['children'])==4 and {x['name']:x['returncode'] for x in s['cleanup']['children']}=={'primary':0,'calc':255,'openbox':0,'xvfb':0},'terminal cleanup')
 require(s['effect']['after_all_owned_processes_terminal'] is True and s['effect']['success'] is False and s['effect']['actual_nonempty_cells']=={},'failed persisted task misclassified')
 return {'status':'PASS_FAILURE_AND_PIXEL_EVIDENCE_AUDIT','scope':'visible cell reading / preserved expired-lease failure; task success=false; no performance comparison'}
if __name__=='__main__':print(json.dumps(check(load(Path(__file__).resolve().parent)),indent=2))
