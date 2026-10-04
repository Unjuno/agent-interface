import pathlib,json,subprocess,time,traceback,hashlib,os
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Point,Size
O=pathlib.Path('/out');rows=[];errors=[];docs=[];proc=None;desktop=None
def prop(k,v):
 p=PropertyValue();p.Name=k;p.Value=v;return p
try:
 proc=subprocess.Popen(['libreoffice','-env:UserInstallation=file:///tmp/draw2122L02','--headless','--nologo','--nodefault','--norestore','--accept=socket,host=127.0.0.1,port=22133;urp;StarOffice.ComponentContext'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);deadline=time.monotonic()+12
 while True:
  try:ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22133;urp;StarOffice.ComponentContext');break
  except Exception:
   if time.monotonic()>deadline:raise
   time.sleep(.1)
 desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
 for case in ['stable_unlocked','stable_locked','conflict_locked','unknown_locked','blind_stale_negative']:
  for arm in (['negative'] if case=='blind_stale_negative' else (['fresh_read_reference','model'] if case in ['stable_locked','unknown_locked'] else ['model','fresh_read_reference'])):
   name=case+'__'+arm;row={'case':case,'arm':arm,'id':name,'events':[]};rows.append(row);started=time.monotonic_ns()
   doc=desktop.loadComponentFromURL('private:factory/sdraw','_blank',0,(prop('Hidden',True),));docs.append(doc);page=doc.getDrawPages().getByIndex(0);manager=doc.getUndoManager();manager.lock()
   targets={}
   for label,x in [('A',1000),('B',2000)]:
    s=doc.createInstance('com.sun.star.drawing.RectangleShape');s.setName(label);s.setPosition(Point(x,1000));s.setSize(Size(500,500));page.add(s);targets[label]=s
   if case=='stable_unlocked':manager.unlock()
   def snap(stage):
    objects=[]
    for i in range(page.getCount()):
     s=page.getByIndex(i);p=s.getPosition();z=s.getSize();objects.append({'name':s.getName(),'position':[p.X,p.Y],'size':[z.Width,z.Height]})
    q={'stage':stage,'objects':objects,'locked':manager.isLocked(),'titles':list(manager.getAllUndoActionTitles())};row['events'].append(q);return q
   initial=snap('initial_read')
   if case in ['conflict_locked','unknown_locked','blind_stale_negative']:
    w=subprocess.run(['/usr/bin/python3','/study/writer.py'],capture_output=True,timeout=10);(O/(name+'.writer.stdout.json')).write_bytes(w.stdout);(O/(name+'.writer.stderr.log')).write_bytes(w.stderr);row['writer_exit']=w.returncode
    if w.returncode:raise RuntimeError('writer_failed:'+name)
    row['writer']=json.loads(w.stdout)
   current=snap('after_writer')
   if arm=='model':
    request={'case':case,'task':'Move A +200 horizontally from its latest position; preserve B and external changes. An old planned absolute target was1200. Undo is unqualified for direct Position. Choose COMMIT to use initial plan only if current state agrees; RECHECK to reread latest state before computing relative move; ABORT or SAVE_AS_NEW to decline this in-place task. Undo lock is recording state, not exclusion. You do not have authority to supply coordinates.','initial':initial,'current':None if case=='unknown_locked' else current,'current_status':'unavailable' if case=='unknown_locked' else 'observed','model_non_authoritative':True}
    path=O/(name+'.request.json');temp=O/(name+'.request.tmp');temp.write_text(json.dumps(request));temp.rename(path);reply=O/(name+'.response.json');deadline=time.monotonic()+60
    while not reply.exists():
     if time.monotonic()>deadline:raise TimeoutError('model_reply:'+name)
     time.sleep(.1)
    response=json.loads(reply.read_text());row['response']=response
    if response.get('transport_ok') is not True:raise RuntimeError('model_transport:'+name)
    action=response['answer']['action']
   elif arm=='fresh_read_reference':action='RECHECK'
   else:action='BLIND_STALE'
   row['action']=action
   if action=='RECHECK':source=snap('rechecked_current')
   else:source=initial
   admission=snap('admission_read');same=admission['objects']==source['objects'];row['current_guard_matches']=same
   setter=targets['A'];p=setter.getPosition();z=setter.getSize();bound={'name':setter.getName(),'position':[p.X,p.Y],'size':[z.Width,z.Height]};row['bound_state']=bound;row['membership_matches']=sum(setter==page.getByIndex(i) for i in range(page.getCount()));row['bound_guard']=bound==source['objects'][0] and row['membership_matches']==1
   if action=='BLIND_STALE' or (action in ['COMMIT','RECHECK'] and same and row['bound_guard']):
    p=setter.getPosition();target=source['objects'][0]['position'][0]+200;setter.setPosition(Point(target,p.Y));row['input_mutations']=1;row['disposition']='SETTER_RETURNED_EFFECT_UNVERIFIED'
   else:row['input_mutations']=0;row['disposition']='REFUSED_STALE' if action=='COMMIT' and not same else 'DECLINED'
   final=snap('final');obs=subprocess.run(['/usr/bin/python3','/study/observer.py'],capture_output=True,timeout=10);(O/(name+'.observer.stdout.json')).write_bytes(obs.stdout);(O/(name+'.observer.stderr.log')).write_bytes(obs.stderr);row['observer_exit']=obs.returncode;row['observer']=json.loads(obs.stdout) if obs.returncode==0 else None;file=O/(name+'.fodg');doc.storeAsURL(uno.systemPathToFileUrl(str(file)),(prop('FilterName','OpenDocument Drawing Flat XML'),prop('Overwrite',True)));row['saved_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();row['elapsed_ns']=time.monotonic_ns()-started
   doc.close(True);docs.remove(doc)
   (O/'RAW.json').write_text(json.dumps({'rows':rows,'errors':errors},indent=2))
except Exception as e:errors.append({'type':type(e).__name__,'message':str(e),'trace':traceback.format_exc()})
finally:
 for d in docs:
  try:d.close(True)
  except Exception as e:errors.append({'close':str(e)})
 if desktop:
  try:desktop.terminate()
  except Exception as e:errors.append({'terminate':str(e)})
 if proc:
  try:stdout,stderr=proc.communicate(timeout=8)
  except subprocess.TimeoutExpired:proc.terminate();stdout,stderr=proc.communicate(timeout=3);errors.append({'cleanup':'fallback_terminate'})
  (O/'soffice.stdout.log').write_bytes(stdout);(O/'soffice.stderr.log').write_bytes(stderr)
 result={'rows':rows,'errors':errors,'parent_exit':None if proc is None else proc.returncode,'controller_pid':os.getpid(),'version':subprocess.run(['libreoffice','--version'],capture_output=True,text=True).stdout.strip(),'cgroup':{p:pathlib.Path('/sys/fs/cgroup/'+p).read_text().strip() for p in ['cpu.max','memory.max','pids.max']}}
 (O/'RAW.json').write_text(json.dumps(result,indent=2));print(json.dumps({'rows':len(rows),'errors':errors,'parent_exit':result['parent_exit']}))
raise SystemExit(bool(errors))
