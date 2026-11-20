import hashlib,json
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
SAMPLE=json.loads((HERE/'SAMPLE.json').read_text()); LABELS={x['code']:x for x in json.loads((HERE/'BLIND_LABELS.json').read_text())['labels']}; BASE=json.loads((HERE/'OUTPUT.json').read_text())
RELATIVE=Path('research/doom/results/map01-v39-coast-liveness-live-01/runtime')
ROOT=next((parent/RELATIVE for parent in Path(__file__).resolve().parents if (parent/RELATIVE).is_dir()), None)
if ROOT is None:
 ROOT=Path(__file__).resolve().parents[2]/'work'/'pr7662-audit-chronology'/RELATIVE
def count(path):
 with Image.open(path) as im: raw=list(im.convert('RGB').crop((450,250,830,520)).getdata())
 w,h=380,270; mask=bytearray(w*h); yellow=red=0
 for i,(r,g,b) in enumerate(raw):
  y=r>180 and g>100 and b<100 and r>.8*g and g>1.5*b
  q=r>70 and r>1.25*g and r>1.25*b
  yellow+=y;red+=q;mask[i]=y or q
 seen=bytearray(w*h); largest=0
 for i,v in enumerate(mask):
  if not v or seen[i]:continue
  seen[i]=1; stack=[i]; area=0
  while stack:
   j=stack.pop();area+=1; yy,xx=divmod(j,w)
   for dy in (-1,0,1):
    for dx in (-1,0,1):
     if not (dx or dy):continue
     nx,ny=xx+dx,yy+dy
     if 0<=nx<w and 0<=ny<h:
      k=ny*w+nx
      if mask[k] and not seen[k]:seen[k]=1;stack.append(k)
  largest=max(largest,area)
 return yellow,red,largest
rows=[]
for e in SAMPLE['entries']:
 path=ROOT/f"{e['sequence']:03}.png"; raw=path.read_bytes(); assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256']
 y,r,m=count(path); label=LABELS[e['code']]
 rows.append({'code':e['code'],'sequence':e['sequence'],'label':label['enemy_visible'],'confidence':label['confidence'],'yellow_count':y,'red_count':r,'largest_component':m,'candidate_positive':m>=8,'source_sha256':e['sha256']})
# Score only determinate labels.
truth=[x for x in rows if x['label'] in ('present','absent')]
tp=sum(x['candidate_positive'] and x['label']=='present' for x in truth);fp=sum(x['candidate_positive'] and x['label']=='absent' for x in truth);fn=sum((not x['candidate_positive']) and x['label']=='present' for x in truth);tn=sum((not x['candidate_positive']) and x['label']=='absent' for x in truth)
baseline={'tp':3,'fp':0,'fn':13,'tn':18,'uncertain_excluded':2}
result={'experiment_id':'issue59-v39-color-component-screen-a01-20261008','candidate_confusion':{'tp':tp,'fp':fp,'fn':fn,'tn':tn,'uncertain_excluded':2},'published_yellow_baseline':baseline,'rows':sorted(rows,key=lambda x:x['code'])}
(HERE/'CANDIDATE_OUTPUT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'candidate_confusion':result['candidate_confusion'],'baseline':baseline,'sample_frames':len(rows)},sort_keys=True))

