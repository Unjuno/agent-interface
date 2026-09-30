from pathlib import Path
import subprocess,json,hashlib,tarfile,io,base64,sys,importlib.util
from PIL import Image
r=Path('/var/tmp/agent-interface-integrated-main');out=r/'results-local/exact-image-intake-01';out.mkdir(exist_ok=False)
frozen='research/observation_gating/results/frozen-a1r3/source/exact_gate.py'
source=subprocess.check_output(['git','show','HEAD:'+frozen],cwd=r)
(out/'exact_gate.py').write_bytes(source)
tests=subprocess.check_output(['git','show','HEAD:research/observation_gating/results/frozen-a1r3/source/test_exact_gate.py'],cwd=r)
(out/'test_exact_gate.py').write_bytes(tests)
sys.path.insert(0,str(out));from exact_gate import ExactGate,Frame,Receiver
result={'scope':'offline exact reconstruction of retained primary Calc streams; no live capture/input/model calls or timing comparison','source':{'path':frozen,'sha256':hashlib.sha256(source).hexdigest(),'blob':subprocess.check_output(['git','rev-parse','HEAD:'+frozen],cwd=r,text=True).strip()},'streams':[]}
for name in ['calc-compact-primary-01','public-review-live-01','target-review-request-primary-01']:
 path=r/'runtime/results'/name/'raw.tar.gz';archive_sha=hashlib.sha256(path.read_bytes()).hexdigest()
 with tarfile.open(path) as archive:
  members=[x for x in archive.getmembers() if x.isfile() and '/host/reply-' in x.name and x.name.endswith('.json')]
  members.sort(key=lambda x:int(x.name.rsplit('reply-',1)[1][:-5]))
  gate=ExactGate('O1',name);receiver=Receiver(name);rows=[];prior=None;images=0;suppressed=0;png_bytes=0;omitted=0
  for member in members:
   raw=archive.extractfile(member).read();reply=json.loads(raw);content=reply.get('result',{}).get('content',[])
   pictures=[x for x in content if x['type']=='image'];context=tuple(x['text'] for x in content if x['type']=='text')
   row={'member':member.name,'reply_sha256':hashlib.sha256(raw).hexdigest(),'attempt':reply.get('id'),'image_count':len(pictures),'text_sha256':[hashlib.sha256(x.encode()).hexdigest() for x in context]}
   if not pictures:rows.append(row);continue
   if len(pictures)!=1:raise ValueError('ambiguous images')
   encoded=base64.b64decode(pictures[0]['data'],validate=True)
   im=Image.open(io.BytesIO(encoded));im.load();frame=Frame(im.width,im.height,im.mode,im.tobytes())
   report=json.loads(context[0]);reference=report.get('image_reference',{});observation=report.get('observation_report',{}).get('observation',{})
   recorded=reference.get('recorded_capture',observation)
   digest=hashlib.sha256(encoded).hexdigest();declared=reference.get('sha256',observation.get('artifact',{}).get('sha256'))
   if digest!=declared:raise ValueError('capture artifact hash mismatch')
   update=gate.push(frame,observed_ns=recorded['capture_started_ns'],action_id=str(reply['id']),context=context)
   decoded=receiver.accept(update)
   if decoded!=frame or update.context!=context or update.observed_ns!=recorded['capture_started_ns']:raise ValueError('reconstruction/context loss')
   expected=prior is not None and (prior.width,prior.height,prior.mode,prior.pixels)==(frame.width,frame.height,frame.mode,frame.pixels)
   if (update.frame is None)!=expected:raise ValueError('independent equality disagreement')
   row.update(image_sha256=digest,png_bytes=len(encoded),dimensions=[im.width,im.height],mode=im.mode,sequence=update.sequence,base_sequence=update.base_sequence,omitted=update.frame is None,metadata_preserved=True,pixels_reconstructed=True,capture_started_ns=recorded['capture_started_ns'],native_window_id=recorded['native_window_id'])
   images+=1;png_bytes+=len(encoded)
   if update.frame is None:suppressed+=1;omitted+=len(encoded)
   prior=frame;rows.append(row)
  result['streams'].append({'archive':str(path.relative_to(r)),'archive_sha256':archive_sha,'calls':len(members),'images':images,'omitted_images':suppressed,'png_bytes':png_bytes,'omitted_png_bytes':omitted,'rows':rows})
result['totals']={k:sum(s[k] for s in result['streams']) for k in ['calls','images','omitted_images','png_bytes','omitted_png_bytes']}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
p=subprocess.run([sys.executable,'-m','unittest','-v','test_exact_gate'],cwd=out,capture_output=True,text=True)
(out/'controls.json').write_text(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
if p.returncode:raise RuntimeError('frozen construction controls failed')
print(result['totals']);print('frozen controls passed')
