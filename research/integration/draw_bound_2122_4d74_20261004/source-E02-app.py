import pathlib,json,subprocess,time,traceback,hashlib,os
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Point,Size
O=pathlib.Path('/out');rows=[];errors=[];docs=[];proc=None;desktop=None
def prop(k,v):
 p=PropertyValue();p.Name=k;p.Value=v;return p
try:
 proc=subprocess.Popen(['libreoffice','-env:UserInstallation=file:///tmp/draw2122E02','--headless','--nologo','--nodefault','--norestore','--accept=socket,host=127.0.0.1,port=22125;urp;StarOffice.ComponentContext'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);deadline=time.monotonic()+12
 while True:
  try:ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22125;urp;StarOffice.ComponentContext');break
  except Exception:
   if time.monotonic()>deadline:raise
   time.sleep(.1)
 desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
 for index,hold_reference in enumerate([False,True,True,False,True,False,False,True]):
  wait_seconds=0;case='hold_'+str(hold_reference)+'_'+str(index)
  for arm in ['fresh_read_reference']:
   name=case+'__'+arm;row={'case':case,'arm':arm,'id':name,'events':[]};rows.append(row);started=time.monotonic_ns()
   doc=desktop.loadComponentFromURL('private:factory/sdraw','_blank',0,(prop('Hidden',True),));docs.append(doc);page=doc.getDrawPages().getByIndex(0);manager=doc.getUndoManager();manager.lock()
   for label,x in [('A',1000),('B',2000)]:
    s=doc.createInstance('com.sun.star.drawing.RectangleShape');s.setName(label);s.setPosition(Point(x,1000));s.setSize(Size(500,500));page.add(s)
   if case=='stable_unlocked':manager.unlock()
   def snap(stage):
    objects=[]
    for i in range(page.getCount()):
     s=page.getByIndex(i);p=s.getPosition();z=s.getSize();objects.append({'name':s.getName(),'position':[p.X,p.Y],'size':[z.Width,z.Height]})
    q={'stage':stage,'objects':objects,'locked':manager.isLocked(),'titles':list(manager.getAllUndoActionTitles())};row['events'].append(q);return q
   held_shape=page.getByIndex(0) if hold_reference else None;row['hold_reference']=hold_reference;initial=snap('initial_read')
   if True:
    w=subprocess.run(['/usr/bin/python3','/study/writer.py'],capture_output=True,timeout=10);(O/(name+'.writer.stdout.json')).write_bytes(w.stdout);(O/(name+'.writer.stderr.log')).write_bytes(w.stderr);row['writer_exit']=w.returncode
    if w.returncode:raise RuntimeError('writer_failed:'+name)
    row['writer']=json.loads(w.stdout)
   current=snap('after_writer')
   row['requested_wait_seconds']=wait_seconds;wait_start=time.monotonic_ns();time.sleep(wait_seconds);row['actual_wait_ns']=time.monotonic_ns()-wait_start
   action='RECHECK'
   row['action']=action
   if action=='RECHECK':source=snap('rechecked_current')
   else:source=initial
   admission=snap('admission_read');same=admission['objects']==source['objects'];row['current_guard_matches']=same
   if action=='BLIND_STALE' or (action in ['COMMIT','RECHECK'] and same):
    p=page.getByIndex(0).getPosition();target=source['objects'][0]['position'][0]+200;arg=Point(target,p.Y);row['setter_argument']=[arg.X,arg.Y];row['setter_start_ns']=time.monotonic_ns();setter_shape=held_shape if hold_reference else page.getByIndex(0);row['setter_name']=setter_shape.getName();row['setter_type']=setter_shape.getShapeType();setter_shape.setPosition(arg);row['setter_proxy_position']=[setter_shape.getPosition().X,setter_shape.getPosition().Y];row['setter_end_ns']=time.monotonic_ns();row['input_mutations']=1;row['disposition']='APPLIED'
   else:row['input_mutations']=0;row['disposition']='REFUSED_STALE' if action=='COMMIT' and not same else 'DECLINED'
   final=snap('final');row['first_final_ns']=time.monotonic_ns();
   time.sleep(.1);snap('after_100ms');time.sleep(.9);snap('after_1s');observer=subprocess.run(['/usr/bin/python3','/study/observer.py'],capture_output=True,timeout=10);(O/(name+'.observer.stdout.json')).write_bytes(observer.stdout);(O/(name+'.observer.stderr.log')).write_bytes(observer.stderr);row['observer_exit']=observer.returncode;row['observer']=json.loads(observer.stdout) if observer.returncode==0 else None;file=O/(name+'.fodg');doc.storeAsURL(uno.systemPathToFileUrl(str(file)),(prop('FilterName','OpenDocument Drawing Flat XML'),prop('Overwrite',True)));row['saved_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();row['elapsed_ns']=time.monotonic_ns()-started
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
