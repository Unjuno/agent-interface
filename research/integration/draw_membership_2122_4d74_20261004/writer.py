import uno,json,os,sys
from com.sun.star.awt import Point,Size
local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);ctx=resolver.resolve('uno:socket,host=127.0.0.1,port=22126;urp;StarOffice.ComponentContext');desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx);enum=desktop.getComponents().createEnumeration();docs=[]
while enum.hasMoreElements():docs.append(enum.nextElement())
if len(docs)!=1:raise RuntimeError('unique_document')
doc=docs[0];page=doc.getDrawPages().getByIndex(0);before=[];after=[];old=page.getByIndex(0)
for i,x in [(0,1700),(1,2700)]:
 s=page.getByIndex(i);p=s.getPosition();before.append([s.getName(),p.X,p.Y]);s.setPosition(Point(x,p.Y))
replaced=sys.argv[1]=='replace'
if replaced:
 page.remove(old);new=doc.createInstance('com.sun.star.drawing.RectangleShape');new.setName('A');new.setPosition(Point(1700,1000));new.setSize(Size(500,500));new.setPropertyValue('Title','generation1');page.add(new);new.setPropertyValue('ZOrder',0)
for i in range(page.getCount()):
 s=page.getByIndex(i);p=s.getPosition();after.append([s.getName(),p.X,p.Y])
if after!=[['A',1700,1000],['B',2700,1000]]:raise RuntimeError('replacement_order_or_effect_unqualified')
print(json.dumps({'pid':os.getpid(),'before':before,'after':after,'locked':doc.getUndoManager().isLocked(),'replacement_executed':replaced,'page_count':page.getCount(),'new_reference_distinct':None if not replaced else new!=old,'generations':[page.getByIndex(i).getPropertyValue('Title') for i in range(page.getCount())]}))
