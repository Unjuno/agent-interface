import subprocess,json,threading,queue
from pathlib import Path
exe=r'C:/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
p=subprocess.Popen([exe,'app-server','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8')
q=queue.Queue()
def read():
    for line in p.stdout:
        q.put(json.loads(line))
threading.Thread(target=read,daemon=True).start()
def request(i,method,params):
    p.stdin.write(json.dumps({'id':i,'method':method,'params':params})+'\n');p.stdin.flush()
    while True:
        row=q.get(timeout=20)
        if row.get('id')==i:
            if 'error' in row:raise RuntimeError(row['error'])
            return row['result']
try:
    request(1,'initialize',{'clientInfo':{'name':'native-config-read-check','version':'1'}})
    p.stdin.write(json.dumps({'method':'initialized'})+'\n');p.stdin.flush()
    results=[]
    for i,cwd in enumerate([r'C:/Users/junny/Documents/New project',r'C:/Users/junny/Documents/New project/agent-interface-admission-audit'],2):
        result=request(i,'config/read',{'cwd':cwd,'includeLayers':True})
        layers=[]
        for layer in result.get('layers') or []:
            config=layer.get('config') or {}
            target=config.get('mcp_servers',{}).get('agent-interface-native-research')
            layers.append({'name':layer.get('name'),'disabledReason':layer.get('disabledReason'),'contains_target_server':target is not None})
        results.append({'cwd':cwd,'layers':layers,'effective_target_present':'agent-interface-native-research' in result.get('config',{}).get('mcp_servers',{})})
    Path('results-local/effective-mcp-layers.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,ensure_ascii=True))
finally:
    p.stdin.close()
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
