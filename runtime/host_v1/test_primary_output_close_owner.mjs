/** Whole primary owner and real inert relay; close never authorizes replay. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {PassThrough,Writable} from 'node:stream';
import {syncBuiltinESMExports} from 'node:module';
import {createRequire} from 'node:module';
import {mkdir,writeFile,readFile,access} from 'node:fs/promises';
import {join} from 'node:path';
import {runPrimaryStdio} from './primary_stdio.mjs';
const require=createRequire(import.meta.url);
const fsPromises=require('node:fs/promises');
const turn=()=>new Promise(resolve=>setImmediate(resolve));
const fixture=`import {createInterface} from 'node:readline';
import {writeFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
const dir=process.argv[2];let count=0,bytes=0;
const put=(name,v)=>writeFileSync(join(dir,name),JSON.stringify(v)+'\\n',{flag:'wx'});
put('fixture-start.json',{pid:process.pid,ppid:process.ppid});
const guard=setTimeout(()=>{process.exitCode=77;process.stdin.destroy();},5000);
process.stdin.on('data',b=>bytes+=b.length);
const lines=createInterface({input:process.stdin,terminal:false});
lines.on('line',line=>{const r=JSON.parse(line);count++;put('fixture-request.json',r);
const poll=setInterval(()=>{if(existsSync(join(dir,'release.json'))){clearInterval(poll);
process.stdout.write(JSON.stringify({status:'returned',id:r.id,tool:r.tool,next_id:r.id+1,result:{content:[{type:'text',text:JSON.stringify({schema:'own-inert-echo-v1',label:r.arguments.label})}]}})+'\\n');}},5);});
lines.once('close',()=>clearTimeout(guard));
process.on('exit',code=>put('fixture-exit.json',{pid:process.pid,ppid:process.ppid,code,requests:count,request_bytes:bytes}));
`;
async function exists(path){try{await access(path);return true;}catch(error){if(error.code==='ENOENT')return false;throw error;}}
async function until(check){const deadline=Date.now()+3000;while(!await check()){if(Date.now()>deadline)return false;await turn();}return true;}
function absent(pid){try{process.kill(pid,0);return false;}catch(error){if(error.code==='ESRCH')return true;throw error;}}
for(const kind of ['returned','busy'])test('whole owner reconciles original request on silent '+kind+' close',{timeout:10000},async()=>{
  assert.ok(process.env.PRIMARY_FAILURE_EVIDENCE);
  const dir=join(process.env.PRIMARY_FAILURE_EVIDENCE,'output-close-owner',kind);await mkdir(dir,{recursive:true});
  const fixturePath=join(dir,'fixture.mjs');await writeFile(fixturePath,fixture,{flag:'wx'});
  const input=new PassThrough();let callback,settled=0,error,stream='',ready;
  const readySeen=new Promise(resolve=>ready=resolve);
  const foreignClose=()=>{},foreignError=()=>{};
  const output=new Writable({autoDestroy:false,write(chunk,encoding,done){
    stream+=chunk;const row=JSON.parse(String(chunk));
    if(row.status==='ready'){done();ready();}else if(row.status===kind)callback=done;else done();
  }});
  output.on('close',foreignClose);output.on('error',foreignError);
  const config={host:{command:process.execPath,args:[fixturePath,dir],evidenceDirectory:join(dir,'host')},route:'guarded-local',exchangeDirectory:join(dir,'exchange')};
  const owner=runPrimaryStdio(config,{input,output}).then(()=>settled++,failure=>{error=failure;settled++;});
  let beforeRelease,boundary,setupPassed=false,released=false;
  const release=async()=>{if(!released){await writeFile(join(dir,'release.json'),'{}\n',{flag:'wx'});released=true;}};
  try {
    await readySeen;
    input.write(JSON.stringify({id:1,method:'call',args:['interface_clock',{label:'original-held'}]})+'\n');
    assert.equal(await until(()=>exists(join(dir,'fixture-request.json'))),true,'original request reaches actual fixture');
    if(kind==='busy')input.write('{"id":2}\n');else await release();
    assert.equal(await until(()=>typeof callback==='function'),true,'write callback is deliberately held');setupPassed=true;
    const closed=new Promise(resolve=>output.once('close',resolve));output.destroy();await closed;await turn();await turn();
    beforeRelease={settled,code:error?.code??null};
    if(kind==='busy')await release();
    input.end();const observed=await until(()=>settled>0);
    boundary={observed,settled,code:error?.code??null};
  } finally {await release();callback?.();input.end();await owner;await turn();await turn();}
  const start=JSON.parse(await readFile(join(dir,'fixture-start.json')));
  const end=JSON.parse(await readFile(join(dir,'fixture-exit.json')));
  const hostExit=JSON.parse(await readFile(join(dir,'host/exit.json')));
  const rows=stream.trim().split('\n').map(JSON.parse);
  const witness={kind,setup_passed:setupPassed,before_release:beforeRelease,boundary,settlements:settled,
    error:{name:error?.name,message:error?.message,code:error?.code??null},fixture_start:start,fixture_exit:end,host_exit:hostExit,
    fixture_absent:absent(start.pid),statuses:rows.map(row=>row.status),rows,
    listeners:{input_errors:input.listenerCount('error'),output_errors:output.listenerCount('error'),output_closes:output.listenerCount('close'),
      foreign_error:output.listeners('error').includes(foreignError),foreign_close:output.listeners('close').includes(foreignClose)}};
  await writeFile(join(dir,'WITNESS.json'),JSON.stringify(witness,null,2)+'\n',{flag:'wx'});
  await writeFile(join(dir,'output.raw.txt'),stream,{flag:'wx'});
  if(kind==='busy')assert.equal(beforeRelease.settled,0,'accepted relay result stays in custody until release');
  assert.equal(boundary.observed,true,'owner settles before withheld callback is released');
  assert.equal(boundary.code,'PRIMARY_OUTPUT_CLOSED');assert.equal(settled,1);
  assert.equal(end.pid,start.pid);assert.equal(end.ppid,start.ppid);assert.equal(end.code,0);assert.equal(end.requests,1);assert.equal(end.request_bytes,72);
  assert.deepEqual(hostExit,{code:0,signal:null});assert.equal(witness.fixture_absent,true);
  assert.deepEqual(witness.listeners,{input_errors:0,output_errors:1,output_closes:1,foreign_error:true,foreign_close:true});
  assert.deepEqual(witness.statuses,kind==='busy'?['ready','busy']:['ready','returned']);
});

test('preclosed stdout refuses before launching host or creating its directories',{timeout:5000},async()=>{
  assert.ok(process.env.PRIMARY_FAILURE_EVIDENCE);
  const dir=join(process.env.PRIMARY_FAILURE_EVIDENCE,'preclosed-owner');await mkdir(dir,{recursive:true});
  const marker=join(dir,'host-started.json');const fixturePath=join(dir,'fixture.mjs');
  await writeFile(fixturePath,`import {writeFileSync} from 'node:fs';writeFileSync(${JSON.stringify(marker)},'started');`,{flag:'wx'});
  const input=new PassThrough(),output=new Writable({write(_chunk,_encoding,done){done();}});output.destroy();await turn();await turn();
  const config={host:{command:process.execPath,args:[fixturePath],evidenceDirectory:join(dir,'host')},route:'guarded-local',exchangeDirectory:join(dir,'exchange')};
  let received;try{await runPrimaryStdio(config,{input,output});}catch(error){received=error;}
  assert.equal(received?.code,'PRIMARY_OUTPUT_CLOSED');assert.equal(await exists(marker),false);
  assert.equal(await exists(join(dir,'host')),false);assert.equal(await exists(join(dir,'exchange')),false);
});

test('close during host startup blocks exchange creation and ready publication',{timeout:7000},async()=>{
  assert.ok(process.env.PRIMARY_FAILURE_EVIDENCE);
  const dir=join(process.env.PRIMARY_FAILURE_EVIDENCE,'startup-close');await mkdir(dir,{recursive:true});
  const fixturePath=join(dir,'fixture.mjs');
  const startPath=join(dir,'fixture-start.json');const exitPath=join(dir,'fixture-exit.json');
  const fixture=`import {writeFileSync} from 'node:fs';
import {join} from 'node:path';
const dir=process.argv[2];
writeFileSync(join(dir,'fixture-start.json'),JSON.stringify({pid:process.pid})+'\\n',{flag:'wx'});
process.stdin.resume();
process.on('exit',code=>writeFileSync(join(dir,'fixture-exit.json'),JSON.stringify({pid:process.pid,code})+'\\n',{flag:'wx'}));
`;
  await writeFile(fixturePath,fixture,{flag:'wx'});
  const originalStatfs=fsPromises.statfs;let held=false,releaseGate,enteredGate;
  const gate=new Promise(resolve=>releaseGate=resolve);const entered=new Promise(resolve=>enteredGate=resolve);
  fsPromises.statfs=async(...args)=>{if(!held){held=true;enteredGate();await gate;}return originalStatfs(...args);};
  syncBuiltinESMExports();
  assert.equal((await import('node:fs/promises')).statfs,fsPromises.statfs);
  const input=new PassThrough(),rows=[];
  const output=new Writable({write(chunk,_encoding,done){rows.push(JSON.parse(String(chunk)));done();}});
  const config={host:{command:process.execPath,args:[fixturePath,dir],evidenceDirectory:join(dir,'host')},route:'guarded-local',exchangeDirectory:join(dir,'exchange')};
  let owner,received;
  try {
    owner=runPrimaryStdio(config,{input,output}).then(()=>({status:'resolved'}),error=>{received=error;return {status:'rejected'};});
    await entered;
    const closed=new Promise(resolve=>output.once('close',resolve));output.destroy();await closed;
    releaseGate();
    const settled=await owner;
    assert.deepEqual(settled,{status:'rejected'});
  } finally {
    releaseGate();fsPromises.statfs=originalStatfs;syncBuiltinESMExports();input.destroy();
    if(owner)await owner;
  }
  const start=JSON.parse(await readFile(startPath,'utf8'));const end=JSON.parse(await readFile(exitPath,'utf8'));
  const witness={status:'rejected',error:{code:received?.code??null,message:received?.message},rows,
    fixture_start:start,fixture_exit:end,host_exit:JSON.parse(await readFile(join(dir,'host/exit.json'),'utf8')),
    exchange_directory_created:await exists(join(dir,'exchange')),input_error_listeners:input.listenerCount('error'),
    output_error_listeners:output.listenerCount('error'),output_close_listeners:output.listenerCount('close')};
  await writeFile(join(dir,'WITNESS.json'),JSON.stringify(witness,null,2)+'\n',{flag:'wx'});
  assert.equal(received?.code,'PRIMARY_OUTPUT_CLOSED');assert.equal(rows.some(row=>row.status==='ready'),false);
  assert.deepEqual(witness.host_exit,{code:0,signal:null});assert.equal(end.pid,start.pid);assert.equal(end.code,0);
  assert.equal(witness.exchange_directory_created,false);assert.equal(witness.input_error_listeners,0);
  assert.equal(witness.output_error_listeners,0);assert.equal(witness.output_close_listeners,0);
});
