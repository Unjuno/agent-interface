#!/usr/bin/env python3
import json,sys
from collections import deque
from native_dbus import Client
A11Y,PID=sys.argv[1],int(sys.argv[2])
ACC='org.a11y.atspi.Accessible'; PROP='org.freedesktop.DBus.Properties'; ROOT='/org/a11y/atspi/accessible/root'
c=Client(A11Y)
try:
    names=c.call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','ListNames')['response']['data'][0]
    rows=[]
    for n in names:
        if not n.startswith(':'): continue
        q=c.call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID','s',(n,))
        if q['rc']==0: rows.append((n,q['response']['data'][0]))
    matches=[n for n,p in rows if p==PID]
    if len(matches)!=1: raise SystemExit(json.dumps({'pass':False,'reason':'pid_map','matches':matches,'rows':rows}))
    app=matches[0]; q=deque([ROOT]);seen=set(); found=[]
    while q and len(seen)<512:
        path=q.popleft()
        if path in seen: continue
        seen.add(path)
        role=c.call(app,path,ACC,'GetRoleName'); props=c.call(app,path,PROP,'GetAll','s',(ACC,)); ifaces=c.call(app,path,ACC,'GetInterfaces')
        rn=role['response']['data'][0] if role['rc']==0 else None
        pd=props['response']['data'][0] if props['rc']==0 else {}
        name=''
        if isinstance(pd,dict) and 'Name' in pd:
            v=pd['Name']; name=v.get('data','') if isinstance(v,dict) else str(v)
        iv=ifaces['response']['data'][0] if ifaces['rc']==0 else []
        if rn=='button' and name and 'org.a11y.atspi.Action' in iv:
            found.append({'path':path,'name':name,'role':rn,'interfaces':iv})
            if name in {'Advanced mode','Reset to simple snapping mode','Open Collections Editor'}: break
        ch=c.call(app,path,ACC,'GetChildren')
        if ch['rc']==0:
            for bus,child in ch['response']['data'][0]:
                if bus==app: q.append(child)
    print(json.dumps({'pass':bool(found),'app_bus':app,'pid':PID,'visited':len(seen),'widget':found[0] if found else None,'known_widget':next((x for x in found if x['name'] in {'Advanced mode','Reset to simple snapping mode','Open Collections Editor'}),None)},sort_keys=True))
finally: c.close()
