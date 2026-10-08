import uno,json,os
local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22132;urp;StarOffice.ComponentContext');desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx);enum=desktop.getComponents().createEnumeration();docs=[]
while enum.hasMoreElements():docs.append(enum.nextElement())
if len(docs)!=1:raise RuntimeError('unique_owned_document_required')
doc=docs[0];page=doc.getDrawPages().getByIndex(0);rows=[]
for i in range(page.getCount()):
 s=page.getByIndex(i);p=s.getPosition();z=s.getSize();rows.append({'name':s.getName(),'position':[p.X,p.Y],'size':[z.Width,z.Height],'generation':s.getPropertyValue('Title')})
print(json.dumps({'pid':os.getpid(),'objects':rows,'locked':doc.getUndoManager().isLocked()}))
