import json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
b=Path(sys.argv[1]);summary={};T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}';O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
def values(blob):
 root=ET.fromstring(blob);sheets=root.findall('.//'+T+'table');assert len(sheets)==1;sheet=sheets[0];rows=sheet.findall(T+'table-row');assert len(rows)==len(sheet.findall('.//'+T+'table-row'));out=[]
 for ri,row in enumerate(rows):
  col=0
  for cell in row:
   if cell.tag not in (T+'table-cell',T+'covered-table-cell'):continue
   count=int(cell.get(T+'number-columns-repeated','1'));assert cell.get(T+'formula') is None;kind=cell.get(O+'value-type');val=cell.get(O+'value');text=''.join(cell.itertext()).strip()
   if kind is not None or val is not None or text:assert count==1 and int(row.get(T+'number-rows-repeated','1'))==1;out.append((ri,col,kind,val,text))
   col+=count
 return out
for n in ('a03','a04'):
 p=b/('wslc-calc-mcp-delayed-save-20261031-'+n);o=p/'output';read=lambda name:json.loads((o/name).read_text());assert (p/'container.exit').read_text().strip()=='0';r=read('result.json');obs=read('mcp-observe.json');mint=read('mcp-mint.json');first=read('mcp-initial.json');terminal=read('mcp-terminal.json');polls=read('mcp-polls.json');close=read('mcp-close.json');entry=read('entry-result.json');cue=read('filled-cue.json');assert obs['status']=='observed' and hashlib.sha256((o/'mcp-image.png').read_bytes()).hexdigest()==obs['source']['native']['artifact']['sha256'];assert mint['status']=='minted' and mint['source_sequence']==obs['source']['sequence'];assert first['status']=='pending' and not first['release_confirmed'] and first['task_success'] is None and first['replay_allowed'] is False;assert first['call_id']==terminal['call_id']==r['call_id'] and terminal['status']=='completed' and terminal['task_success'] is None and terminal['replay_allowed'] is False and polls and polls[-1]['status']=='completed';rel=terminal['result']['execution']['releases'];assert rel and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in rel);assert close['status']=='closed' and close['release']['verified'] and r['keys_down']==[] and r['buttons_after']==0;assert len(list((o/'mcp-receipts').rglob('program-*.json')))==1;assert entry['status']=='completed' and cue['cue']=='filled' and all(x['verified'] for x in entry['execution']['releases']);assert r['submitted_ns']<r['terminal_ns']<r['mid_observed_ns']<=r['after_observed_ns'];mid=(o/'mid.fods').read_bytes();after=(o/'after.fods').read_bytes();assert hashlib.sha256(mid).hexdigest()==r['mid_sha256'] and hashlib.sha256(after).hexdigest()==r['after_sha256'] and hashlib.sha256((p/'blank.fods').read_bytes()).hexdigest()==r['baseline_sha256'];assert values(after)==[(0,0,'float','731','731'),(1,0,'float','864','864')]
 if n=='a03':assert values(mid)==values(after) and r['mid_sha256']!=r['baseline_sha256']
 else:
  stop=read('target-stopped.json');resume=read('target-resumed.json');assert stop['state']=='T' and stop['pid']==resume['pid']==r['calc_pid'] and stop['stopped_ns']<r['submitted_ns'] and r['mid_observed_ns']<resume['resumed_ns']<r['after_observed_ns'];assert r['mid_sha256']==r['baseline_sha256'] and values(mid)==[]
 summary[n]={'initial_status':first['status'],'terminal_status':terminal['status'],'same_call_id':True,'task_success':terminal['task_success'],'release_verified':True,'saved_at_terminal':r['mid_sha256']!=r['baseline_sha256'],'saved_after_resume':True,'keys_down':r['keys_down'],'buttons':r['buttons_after']}
print(json.dumps(summary,indent=2))
