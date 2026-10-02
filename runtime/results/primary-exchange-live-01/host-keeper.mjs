import {readFile,writeFile,rename} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const [caseArg,archiveArg,bundleArg,display,targetsArg]=process.argv.slice(2);
const caseDir=resolve(caseArg),bundle=resolve(bundleArg);
const {createInstrumentedRelayClient}=await import(pathToFileURL(join(bundle,'relay_host.mjs')));
const {createPrimaryExchange}=await import(pathToFileURL(join(bundle,'primary_exchange.mjs')));
const host=await createInstrumentedRelayClient({command:'/tmp/agent-interface-mcp-venv/bin/python',args:[resolve(archiveArg),'relay','--','--targets',targetsArg,'--output-directory',join(caseDir,'calls'),'--display',display,'--session-mode','guarded-x11'],evidenceDirectory:join(caseDir,'host')});
const exchange=await createPrimaryExchange({host,route:'guarded-local',directory:join(caseDir,'exchange')});
async function write(path,value){const temp=path+'.tmp';await writeFile(temp,JSON.stringify(value,null,2)+'\n',{flag:'wx'});await rename(temp,path);}
console.log('READY HOST');
try {
  for(let id=1;id<=16;id++){
    const name=String(id).padStart(3,'0')+'.json',path=join(caseDir,'commands',name);
    let request;
    for(;;){try{request=JSON.parse(await readFile(path,'utf8'));break;}catch(e){if(e.code!=='ENOENT')throw e;await new Promise(r=>setTimeout(r,20));}}
    const start=process.hrtime.bigint();
    const result=await exchange.execute(request);
    await write(join(caseDir,'replies',name),{...result,started_ns:start.toString(),ended_ns:process.hrtime.bigint().toString(),exchange_state:exchange.state()});
    console.log('REPLY '+id);
    if(request.method==='call'&&request.args[0]==='interface_close')break;
  }
} catch(error){await write(join(caseDir,'host-exception.json'),{error:String(error),state:exchange.state(),replay_allowed:false});throw error;}
finally {const exit=await host.close();await write(join(caseDir,'host-terminal.json'),{exit,state:exchange.state()});console.log('TERMINAL HOST');}
