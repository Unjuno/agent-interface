import json,pathlib,subprocess,time,traceback,hashlib
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Point,Size
def prop(k,v):
    p=PropertyValue();p.Name=k;p.Value=v;return p
out=pathlib.Path('/out');rows=[];errors=[];docs=[];desktop=None;proc=None
try:
    proc=subprocess.Popen(['libreoffice','-env:UserInstallation=file:///tmp/draw2122D01','--headless','--nologo','--nodefault','--norestore','--accept=socket,host=127.0.0.1,port=22124;urp;StarOffice.ComponentContext'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
    deadline=time.monotonic()+12
    while True:
        try:ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22124;urp;StarOffice.ComponentContext');break
        except Exception:
            if time.monotonic()>deadline:raise
            time.sleep(.1)
    desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
    for case in ['insert_rectangle','move_rectangle']:
        row={'case':case,'events':[]};rows.append(row)
        doc=desktop.loadComponentFromURL('private:factory/sdraw','_blank',0,(prop('Hidden',True),))
        if doc is None:row['disposition']='HOLD_DRAW_FACTORY_UNAVAILABLE';continue
        docs.append(doc);page=doc.getDrawPages().getByIndex(0);manager=doc.getUndoManager()
        def snapshot(stage):
            objects=[]
            for i in range(page.getCount()):
                s=page.getByIndex(i);p=s.getPosition();z=s.getSize()
                objects.append({'name':s.getName(),'type':s.getShapeType(),'position':[p.X,p.Y],'size':[z.Width,z.Height]})
            snap={'stage':stage,'objects':objects,'titles':list(manager.getAllUndoActionTitles()),'undo_possible':manager.isUndoPossible(),'locked':manager.isLocked()}
            row['events'].append(snap);return snap
        shape=doc.createInstance('com.sun.star.drawing.RectangleShape');shape.setName('owned_rectangle');shape.setPosition(Point(1000,1000));shape.setSize(Size(2000,1500))
        if case=='move_rectangle':manager.lock();page.add(shape);manager.unlock()
        before=snapshot('before_operation')
        if case=='insert_rectangle':page.add(shape)
        else:shape.setPosition(Point(4000,3000))
        changed=snapshot('after_operation')
        row['mutation_observed']=before['objects']!=changed['objects']
        if manager.isUndoPossible():
            manager.undo();restored=snapshot('after_undo')
            row['disposition']='RECORDING_QUALIFIED_SCOPED' if restored['objects']==before['objects'] else 'FAIL_WRONG_RESTORATION'
        else:row['disposition']='HOLD_OPERATION_NOT_RECORDED'
        path=out/(case+'.fodg');doc.storeAsURL(uno.systemPathToFileUrl(str(path)),(prop('FilterName','OpenDocument Drawing Flat XML'),prop('Overwrite',True)))
        row['saved_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
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
        (out/'soffice.stdout.log').write_bytes(stdout);(out/'soffice.stderr.log').write_bytes(stderr)
result={'rows':rows,'errors':errors,'parent_exit':None if proc is None else proc.returncode,'version':subprocess.run(['libreoffice','--version'],capture_output=True,text=True).stdout.strip(),'cgroup':{p:pathlib.Path('/sys/fs/cgroup/'+p).read_text().strip() for p in ['cpu.max','memory.max','pids.max']},'scope':'actual headless Draw direct UNO recording eligibility only; no model/GUI/independent writer/task benefit'}
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
