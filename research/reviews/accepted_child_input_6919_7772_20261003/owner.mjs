/** Actual host modules; the input fault and downstream task/release metadata are fixtures. */
import {PassThrough} from 'node:stream';
import {existsSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [directory,source,python,peer,mode,boundary] = process.argv.slice(2);
const {runPrimaryStdio} = await import(pathToFileURL(join(source,'primary_stdio.mjs')).href);
const input = new PassThrough(), output = new PassThrough();
let ready=false, remainder='', triggered=false;
const put=(name,value)=>writeFileSync(join(directory,name),JSON.stringify(value)+'\n',{flag:'wx'});
output.on('data',chunk=>{
  process.stdout.write(chunk);remainder+=chunk.toString();
  let pos;
  while((pos=remainder.indexOf('\n'))>=0){
    const line=remainder.slice(0,pos);remainder=remainder.slice(pos+1);
    if(JSON.parse(line).status==='ready')ready=true;
  }
});
const config={route:'guarded-local',exchangeDirectory:join(directory,'exchange'),
  host:{command:python,args:[peer,directory,mode],evidenceDirectory:join(directory,'host')}};
const ownedFault = new Error('owned-fixture-input-fault');
const poll=setInterval(()=>{
  if(!ready||triggered||!existsSync(join(directory,'trigger-boundary')))return;
  triggered=true;
  put('boundary-injected.json',{kind:boundary});
  if(boundary==='input-error'){
    input.once('close',()=>put('boundary-observed.json',{kind:'close'}));
    input.destroy(ownedFault);
  }else{
    input.once('end',()=>put('boundary-observed.json',{kind:'end'}));
    input.end();
  }
},5);
// Collector permits exactly one line only after this owner has emitted ready.
const sendPoll=setInterval(()=>{
  if(!ready||!existsSync(join(directory,'send-command')))return;
  clearInterval(sendPoll);
  input.write(JSON.stringify({id:1,method:'input',args:['synthetic-control',[0,0],'click',[]]})+'\n');
},5);
const guard=setTimeout(()=>{put('owner-deadline.json',{code:72});process.exit(72);},9000);
try{
  await runPrimaryStdio(config,{input,output});
  put('owner-result.json',{status:'resolved',input_error_listeners:input.listenerCount('error'),output_error_listeners:output.listenerCount('error')});
}catch(error){
  put('owner-result.json',{status:'rejected',same_error:error===ownedFault,error:String(error),input_error_listeners:input.listenerCount('error'),output_error_listeners:output.listenerCount('error')});
  console.error(String(error));process.exitCode=2;
}finally{clearInterval(poll);clearInterval(sendPoll);clearTimeout(guard);}
