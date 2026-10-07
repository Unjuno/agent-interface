import uno,json,os
from com.sun.star.awt import Point
local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22133;urp;StarOffice.ComponentContext')
desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx);enum=desktop.getComponents().createEnumeration();docs=[]
while enum.hasMoreElements():docs.append(enum.nextElement())
if len(docs)!=1:raise RuntimeError('unique_owned_document_required')
doc=docs[0];page=doc.getDrawPages().getByIndex(0)
before=[];after=[]
for i,x in [(0,1700),(1,2700)]:
 s=page.getByIndex(i);p=s.getPosition();before.append([s.getName(),p.X,p.Y]);s.setPosition(Point(x,p.Y));p=s.getPosition();after.append([s.getName(),p.X,p.Y])
print(json.dumps({'pid':os.getpid(),'before':before,'after':after,'locked':doc.getUndoManager().isLocked()}))
