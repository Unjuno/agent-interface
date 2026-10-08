import hashlib,json,pathlib,sys
sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'decoded-packet.json').read_text(encoding='utf-8'))
m=p['members']; assert len(m)==79 and len({x['path'] for x in m})==79
index=[]
for n,x in enumerate(m):
    data=x['text'].encode('utf-8')
    assert type(x['bytes']) is int and len(data)==x['bytes']
    assert hashlib.sha256(data).hexdigest()==x['sha256']
    name=f'member-{n:03d}.txt'
    with (root/name).open('xb') as f:f.write(data)
    index.append({'path':x['path'],'local_inert':name,'bytes':len(data),'sha256':x['sha256']})
with (root/'MEMBER_READBACK.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(index,f,indent=2);f.write('\n')
selected=['unit/run-stock.js.txt','unit/UI_EVENTS.jsonl','unit/UI_RAW.json','unit/stock/examples/javascript-es5/dist/view.js','unit/stock/examples/javascript-es5/dist/controller.js','unit/stock/examples/javascript-es5/dist/app.js']
print(json.dumps({'read_back':len(index),'member_bytes':sum(x['bytes'] for x in index)},ensure_ascii=False))
for path in selected:
    x=next(x for x in m if x['path']==path)
    print(json.dumps({'path':path,'text':x['text']},ensure_ascii=False))
