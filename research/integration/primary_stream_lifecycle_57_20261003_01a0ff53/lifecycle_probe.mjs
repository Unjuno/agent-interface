import {PassThrough,Writable} from 'node:stream';
import {readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const [scenario,source,directory]=process.argv.slice(2);
if(!['ready_input','ready_output','terminal_output','normal_eof'].includes(scenario))throw Error('unknown fixed scenario');
const {runPrimaryStdio}=await import(pathToFileURL(join(source,'primary_stdio.mjs')));
const input=new PassThrough();
const fault=Error('injected '+scenario+' channel failure');
let readyResolve,releaseReady,settled=false;
const ready=new Promise(resolve=>{readyResolve=resolve;});
const events=[],writeIntents=[];
const record=value=>{events.push(value);console.log(JSON.stringify(value));};
const output=new Writable({write(chunk,_encoding,callback){
  const value=JSON.parse(chunk.toString());writeIntents.push(value);
  record({kind:'write_enter',status:value.status});
  if(value.status==='ready'){
    if(scenario==='ready_input')releaseReady=()=>{record({kind:'write_ack',status:'ready'});callback();};
    else if(scenario==='ready_output'){record({kind:'write_error_callback',status:'ready'});callback(fault);}
    else {record({kind:'write_ack',status:'ready'});callback();}
    readyResolve();
  }else if(scenario==='terminal_output'){
    record({kind:'write_error_callback',status:value.status});callback(fault);
  }else {record({kind:'write_ack',status:value.status});callback();}
}});
const config={host:{command:process.execPath,args:[fileURLToPath(new URL('./relay_fixture.mjs',import.meta.url)),directory],evidenceDirectory:join(directory,'host')},route:'guarded-local',exchangeDirectory:join(directory,'exchange')};
const initialListeners={input:input.listenerCount('error'),output:output.listenerCount('error')};
const owner=runPrimaryStdio(config,{input,output}).then(
  ()=>{settled=true;record({kind:'owner_resolved'});return {kind:'resolved'};},
  error=>{settled=true;record({kind:'owner_rejected',message:error.message,original_identity:error===fault});return {kind:'rejected',message:error.message,original_identity:error===fault};}
);
await ready;
if(scenario==='ready_input'){
  record({kind:'input_destroy',ready_write_unacknowledged:true});input.destroy(fault);
  await new Promise(resolve=>setImmediate(resolve));
  record({kind:'after_input_turn',settled});
  releaseReady();
}else if(scenario!=='ready_output'){
  record({kind:'input_eof'});input.end();
}
const outcome=await owner;
await new Promise(resolve=>setImmediate(resolve));
const exit=JSON.parse(await readFile(join(directory,'host/exit.json')));
const listeners={input:input.listenerCount('error'),output:output.listenerCount('error')};
const summary={scenario,outcome,exit,initialListeners,listeners,writeIntents,events};
await writeFile(join(directory,'owner.summary.json'),JSON.stringify(summary,null,2)+'\n',{flag:'wx'});
record({kind:'probe_complete',scenario});
