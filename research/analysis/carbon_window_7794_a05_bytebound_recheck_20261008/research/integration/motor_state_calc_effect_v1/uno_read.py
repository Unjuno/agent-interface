import json,sys,time,uno
port=int(sys.argv[1]); local=uno.getComponentContext(); resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local); ctx=None
for _ in range(50):
 try: ctx=resolver.resolve(f'uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext'); break
 except Exception: time.sleep(.05)
if ctx is None: raise SystemExit('NO_CONNECT')
desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx); doc=desktop.getCurrentComponent(); c=doc.Sheets.getByIndex(0).getCellRangeByName('A1')
print(json.dumps({'string':c.String,'value':c.Value,'formula':c.Formula},sort_keys=True))
