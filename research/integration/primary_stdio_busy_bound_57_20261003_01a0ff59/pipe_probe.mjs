// Finite ordinary engineering probe of the real primary CLI and child pipes.
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
const [sourceDirectory,outputDirectory]=process.argv.slice(2);
if(!sourceDirectory||!outputDirectory)throw Error('source and fresh output directories required');
const root=resolve(outputDirectory);await mkdir(root);
const source=resolve(sourceDirectory);
const fixture=`const fs=require('node:fs');const rl=require('node:readline');
rl.createInterface({input:process.stdin}).on('line',line=>{
fs.appendFileSync(process.argv[1],line+'\\n');const r=JSON.parse(line);
setTimeout(()=>process.stdout.write(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,
result:{isError:false,content:[{type:'text',text:'{"status":"closed"}'}]}})+'\\n'),50);
});`;
const config={host:{command:process.execPath,args:['-e',fixture,join(root,'relay-received.jsonl')],
evidenceDirectory:join(root,'host')},route:'guarded-local',exchangeDirectory:join(root,'exchange')};
await writeFile(join(root,'config.json'),JSON.stringify(config)+'\n',{flag:'wx'});
const commands=[1,2,3].map(id=>({id,method:'call',args:['interface_close',{}]}));
const input=commands.map(x=>JSON.stringify(x)+'\n').join('');
await writeFile(join(root,'stdin.jsonl'),input,{flag:'wx'});
const child=spawn(process.execPath,[join(source,'runtime/host_v1/primary_stdio.mjs'),'--config',join(root,'config.json')],{stdio:['pipe','pipe','pipe'],windowsHide:true});
let stdout='',stderr='',ready=false;
child.stdout.on('data',chunk=>{stdout+=chunk;});child.stderr.on('data',chunk=>{stderr+=chunk;});
const lines=createInterface({input:child.stdout});
lines.on('line',line=>{
  const row=JSON.parse(line);
  if(row.status==='ready'&&!ready){ready=true;child.stdin.end(input);}
});
child.stdin.on('error',error=>{stderr+='stdin error: '+error+'\n';});
const start=new Date().toISOString();
const exit=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',(code,signal)=>resolve({code,signal}));});
const end=new Date().toISOString();
await writeFile(join(root,'stdout.jsonl'),stdout,{flag:'wx'});
await writeFile(join(root,'stderr.txt'),stderr,{flag:'wx'});
await writeFile(join(root,'process.json'),JSON.stringify({node:process.version,platform:process.platform,arch:process.arch,started_utc:start,ended_utc:end,ready_observed:ready,exit})+'\n',{flag:'wx'});
console.log(JSON.stringify({output:root,ready,exit,rows:stdout.trim().split('\n').filter(Boolean).map(x=>JSON.parse(x).status)}));
