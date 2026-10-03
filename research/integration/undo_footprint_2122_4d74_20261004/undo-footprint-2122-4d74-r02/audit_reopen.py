import pathlib,json,subprocess,time,hashlib,traceback
import uno
from com.sun.star.beans import PropertyValue
R=pathlib.Path(__file__).resolve().parent;O=R/'output';raw=json.loads((O/'raw.json').read_text(encoding='utf-8-sig'));F=json.loads((R/'REOPEN_FREEZE.json').read_text());errors=[];out=[];docs=[];desktop=None;proc=None
def p(k,v):x=PropertyValue();x.Name=k;x.Value=v;return x
try:
    for name,digest in F['files'].items():
        if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:errors.append('hash:'+name)
    proc=subprocess.Popen(['libreoffice','-env:UserInstallation=file:///tmp/reopen2122profile','--headless','--nologo','--nodefault','--norestore','--accept=socket,host=127.0.0.1,port=22123;urp;StarOffice.ComponentContext'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);deadline=time.monotonic()+12
    while True:
        try:ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22123;urp;StarOffice.ComponentContext');break
        except Exception:
            if time.monotonic()>deadline:raise
            time.sleep(.1)
    desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
    if raw['errors'] or raw['parent_exit']!=0:errors.append('original_producer')
    if len(raw['rows'])!=2:errors.append('coverage')
    before=[]
    for row in raw['rows']:
        name=row['case'];path=O/(name+'.fods');blob=path.read_bytes()
        if hashlib.sha256(blob).hexdigest()!=row['saved_sha256']:errors.append('saved:'+name)
        doc=desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(path)),'_blank',0,(p('Hidden',True),p('ReadOnly',True)));docs.append(doc);sheet=doc.Sheets.getByIndex(0);values=[sheet.getCellRangeByName(x).getString() for x in ['A1','B1']];events={e['stage']:e for e in row['events']};b=events['before_undo'];a=events['after_undo'];before.append((b['A1'],b['B1'],b['titles'],b['undo_possible'],b['locked']))
        expected=['','PROTECTED' if name=='single_visible' else '']
        if values!=expected or values!=[a['A1'],a['B1']]:errors.append('reopened:'+name)
        out.append({'case':name,'reopened_cells':values,'read_only':doc.isReadonly(),'sha256':hashlib.sha256(blob).hexdigest()})
        if not doc.isReadonly():errors.append('readonly')
    if len(before)!=2 or before[0]!=before[1] or before[0]!=('OWNED','PROTECTED',['Input'],True,False):errors.append('contrast')
except Exception:errors.append(traceback.format_exc())
finally:
    for doc in docs:
        try:doc.close(True)
        except Exception as e:errors.append('close:'+str(e))
    if desktop:
        try:desktop.terminate()
        except Exception as e:errors.append('terminate:'+str(e))
    if proc:
        try:stdout,stderr=proc.communicate(timeout=8)
        except subprocess.TimeoutExpired:proc.terminate();stdout,stderr=proc.communicate(timeout=3);errors.append('fallback_terminate')
        if proc.returncode!=0:errors.append('reopen_parent_exit')
    for name,digest in F['files'].items():
        if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:errors.append('posthash:'+name)
print(json.dumps({'decision':'SUPPORT_VISIBLE_HISTORY_INSUFFICIENT_SCOPED' if not errors else 'FAIL_OR_HOLD','errors':errors,'rows':out,'parent_exit':None if proc is None else proc.returncode,'scope':'read-only saved-document reopen, no Undo or original producer replay; same-author supplemental audit'},indent=2));raise SystemExit(bool(errors))
