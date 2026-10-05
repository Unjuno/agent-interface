import os,pathlib,subprocess,time,json,traceback,hashlib
import uno
from com.sun.star.beans import PropertyValue
def prop(k,v):p=PropertyValue();p.Name=k;p.Value=v;return p
proc=None;desktop=None;rows=[];errors=[];docs=[]
try:
    proc=subprocess.Popen(['libreoffice','-env:UserInstallation=file:///tmp/undo2122profile','--headless','--nologo','--nodefault','--norestore','--accept=socket,host=127.0.0.1,port=22122;urp;StarOffice.ComponentContext'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
    deadline=time.monotonic()+12
    while True:
        try:ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22122;urp;StarOffice.ComponentContext');break
        except Exception:
            if time.monotonic()>deadline:raise
            time.sleep(.1)
    sm=ctx.ServiceManager;desktop=sm.createInstanceWithContext('com.sun.star.frame.Desktop',ctx);dispatch=sm.createInstanceWithContext('com.sun.star.frame.DispatchHelper',ctx)
    for case in ['single_visible','hidden_attached']:
        doc=desktop.loadComponentFromURL('private:factory/scalc','_blank',0,(prop('Hidden',True),));docs.append(doc);sheet=doc.Sheets.getByIndex(0);manager=doc.getUndoManager();controller=doc.getCurrentController();frame=controller.getFrame();row={'case':case,'events':[]}
        def snap(stage):
            data={'stage':stage,'A1':sheet.getCellRangeByName('A1').getString(),'B1':sheet.getCellRangeByName('B1').getString(),'titles':list(manager.getAllUndoActionTitles()),'undo_possible':manager.isUndoPossible(),'locked':manager.isLocked()};row['events'].append(data);return data
        def enter(address,value):
            sheet.getCellRangeByName(address).setString(value)
        snap('initial')
        if case=='single_visible':
            manager.lock();sheet.getCellRangeByName('B1').setString('PROTECTED');manager.unlock()
        snap('after_unrecorded_setup')
        enter('A1','OWNED');snap('after_visible')
        if not manager.isUndoPossible():row['disposition']='HOLD_OPERATION_NOT_RECORDED';rows.append(row);continue
        if case=='hidden_attached':
            manager.enterHiddenUndoContext();enter('B1','PROTECTED');manager.leaveUndoContext()
        snap('before_undo')
        manager.undo();snap('after_undo')
        out=pathlib.Path('/out')/(case+'.fods');doc.storeAsURL(uno.systemPathToFileUrl(str(out)),(prop('FilterName','OpenDocument Spreadsheet Flat XML'),prop('Overwrite',True)));row['saved_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();row['disposition']='OBSERVED';rows.append(row)
except Exception as e:errors.append({'type':type(e).__name__,'message':str(e),'trace':traceback.format_exc()})
finally:
    for doc in docs:
        try:doc.close(True)
        except Exception as e:errors.append({'cleanup':str(e)})
    if desktop:
        try:desktop.terminate()
        except Exception as e:errors.append({'terminate':str(e)})
    if proc:
        try:stdout,stderr=proc.communicate(timeout=8)
        except subprocess.TimeoutExpired:proc.terminate();stdout,stderr=proc.communicate(timeout=3);errors.append({'cleanup':'fallback_terminate'})
        pathlib.Path('/out/soffice.stdout.log').write_bytes(stdout);pathlib.Path('/out/soffice.stderr.log').write_bytes(stderr)
result={'rows':rows,'errors':errors,'parent_exit':None if proc is None else proc.returncode,'version':subprocess.run(['libreoffice','--version'],capture_output=True,text=True).stdout.strip(),'scope':'fresh disposable LibreOffice UNO/API recording and hidden context only; no model/native GUI/provider; protected label authored separately attributed mutation, not independent writer ownership'}
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
