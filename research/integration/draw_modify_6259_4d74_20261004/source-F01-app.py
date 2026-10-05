import pathlib,json,subprocess,time,traceback,hashlib,os
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Point,Size
O=pathlib.Path('/out');rows=[];errors=[];docs=[];proc=None;desktop=None
def prop(k,v):
 p=PropertyValue();p.Name=k;p.Value=v;return p
try:
 proc=subprocess.Popen(['libreoffice','-env:UserInstallation=file:///tmp/draw6259F01','--headless','--nologo','--nodefault','--norestore','--accept=socket,host=127.0.0.1,port=22130;urp;StarOffice.ComponentContext'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);deadline=time.monotonic()+12
 while True:
  try:ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22130;urp;StarOffice.ComponentContext');break
  except Exception:
   if time.monotonic()>deadline:raise
   time.sleep(.1)
 desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
 for case in ['stable','mutated']:
  row={'id':case,'events':[]};rows.append(row)
  doc=desktop.loadComponentFromURL('private:factory/sdraw','_blank',0,(prop('Hidden',True),));docs.append(doc);page=doc.getDrawPages().getByIndex(0);doc.getUndoManager().lock();held=[]
  for label,x in [('A',1900),('B',2800)]:
   z=doc.createInstance('com.sun.star.drawing.RectangleShape');z.setName(label);z.setPosition(Point(x,1000));z.setSize(Size(500,500));page.add(z);held.append(z)
  def state():
   result=[]
   for i in range(page.getCount()):
    z=page.getByIndex(i);p=z.getPosition();result.append([z.getName(),p.X,p.Y])
   return result
  row['before']=state();row['read_A']=held[0].getPosition().X;row['read_A_completed_ns']=time.monotonic_ns()
  if case=='mutated':
   w=subprocess.run(['/usr/bin/python3','/study/writer.py'],capture_output=True,timeout=10);(O/(case+'.writer.stdout.json')).write_bytes(w.stdout);(O/(case+'.writer.stderr.log')).write_bytes(w.stderr);row['writer_exit']=w.returncode
   if w.returncode:raise RuntimeError('writer_failed')
   row['writer']=json.loads(w.stdout);row['writer_completed_ns']=time.monotonic_ns()
  row['read_B']=held[1].getPosition().X;row['read_B_completed_ns']=time.monotonic_ns();row['split_satisfied']=row['read_A']==1900 and row['read_B']==2700
  row['after']=state();row['fresh_satisfied']=row['after']==[['A',1900,1000],['B',2700,1000]]
  obs=subprocess.run(['/usr/bin/python3','/study/observer.py'],capture_output=True,timeout=10);(O/(case+'.observer.stdout.json')).write_bytes(obs.stdout);(O/(case+'.observer.stderr.log')).write_bytes(obs.stderr);row['observer_exit']=obs.returncode;row['observer']=json.loads(obs.stdout) if obs.returncode==0 else None
  file=O/(case+'.fodg');doc.storeAsURL(uno.systemPathToFileUrl(str(file)),(prop('FilterName','OpenDocument Drawing Flat XML'),prop('Overwrite',True)));row['saved_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();row['controller_mutations_after_setup']=0;doc.close(True);docs.remove(doc)
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
