import {PassThrough,Writable} from 'node:stream';
import {readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const [scenario,source,directory]=process.argv.slice(2);
if(!['pending_success','pending_persistence_failure'].includes(scenario))throw Error('unknown fixed scenario');
const {runPrimaryStdio}=await import(pathToFileURL(join(source,'primary_stdio.mjs')));
const input=new PassThrough(),fault=Error('original pending input failure');
const rows=[],events=[];let readyResolve,settled=false;
const ready=new Promise(resolve=>{readyResolve=resolve;});
const event=value=>{events.push(value);console.log(JSON.stringify(value));};
const output=new Writable({write(chunk,encoding,callback){
  const value=JSON.parse(chunk.toString());rows.push(value);event({kind:'output',status:value.status});callback();
  if(value.status==='ready')readyResolve();
}});
const config={host:{command:process.execPath,args:[fileURLToPath(new URL('./pending_fixture.mjs',import.meta.url)),directory],evidenceDirectory:join(directory,'host')},route:'guarded-local',exchangeDirectory:join(directory,'exchange')};
const owner=runPrimaryStdio(config,{input,output}).then(
  ()=>{throw Error('input failure unexpectedly resolved');},
  error=>{settled=true;event({kind:'owner_rejected',original_identity:error===fault,message:error.message});if(error!==fault)throw error;}
);
await ready;input.write('{"id":1,"method":"call","args":["interface_clock",{}]}\n');
const deadline=Date.now()+3000;let request;
while(!request&&Date.now()<deadline){
  try {request=JSON.parse(await readFile(join(directory,'fixture.request.json')));}
  catch(error){if(error.code!=='ENOENT')throw error;await new Promise(resolve=>setTimeout(resolve,5));}
}
if(!request)throw Error('owned fixture request absent');
event({kind:'actual_request_accepted',request});
if(scenario==='pending_persistence_failure')await writeFile(join(directory,'exchange/original-reply-1.json'),'occupied original slot\n',{flag:'wx'});
input.destroy(fault);event({kind:'input_failure'});
await new Promise(resolve=>setImmediate(resolve));
if(settled)throw Error('owner abandoned the actual pending relay request');
event({kind:'pending_observed_before_release',settled});
await writeFile(join(directory,'release'),'release original reply\n',{flag:'wx'});
event({kind:'reply_released'});await owner;
const exit=JSON.parse(await readFile(join(directory,'host/exit.json')));
const summary={scenario,rows,events,exit,listeners:{input:input.listenerCount('error'),output:output.listenerCount('error')}};
await writeFile(join(directory,'owner.summary.json'),JSON.stringify(summary,null,2)+'\n',{flag:'wx'});event({kind:'probe_complete'});
