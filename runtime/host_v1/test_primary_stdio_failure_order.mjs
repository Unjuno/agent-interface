/** Ordinary owned fixture checks: inner first diagnosis reaches the whole owner. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {PassThrough,Writable} from 'node:stream';
import {mkdir,writeFile,readFile,access} from 'node:fs/promises';
import {join} from 'node:path';
import {runPrimaryStdio} from './primary_stdio.mjs';

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
async function waitFile(path){const deadline=Date.now()+3000;while(!await exists(path)){if(Date.now()>deadline)throw Error('owned fixture request unavailable');await turn();}}
function absent(pid){try{process.kill(pid,0);return false;}catch(error){if(error.code==='ESRCH')return true;throw error;}}

for(const laterChannel of ['input','output'])test('first busy failure survives later '+laterChannel+' error',{timeout:10000},async()=>{
  assert.ok(process.env.PRIMARY_FAILURE_EVIDENCE,'explicit fresh evidence root required');
  const dir=join(process.env.PRIMARY_FAILURE_EVIDENCE,laterChannel);await mkdir(dir,{recursive:true});
  const fixturePath=join(dir,'fixture.mjs');await writeFile(fixturePath,fixture,{flag:'wx'});
  const input=new PassThrough();let busyDone,settled=false,recordedError=null,stream='';
  let ready;const readySeen=new Promise(resolve=>ready=resolve);
  const output=new Writable({autoDestroy:false,write(chunk,_encoding,done){
    stream+=chunk;const row=JSON.parse(String(chunk));
    if(row.status==='ready'){done();ready();}else if(row.status==='busy'){busyDone=done;}else done();
  }});
  const config={host:{command:process.execPath,args:[fixturePath,dir],evidenceDirectory:join(dir,'host')},
    route:'guarded-local',exchangeDirectory:join(dir,'exchange')};
  const started=new Date().toISOString();
  const owner=runPrimaryStdio(config,{input,output}).then(()=>{settled=true;},error=>{recordedError=error;settled=true;});
  let beforeRelease;
  try {
    await readySeen;
    input.write(JSON.stringify({id:1,method:'call',args:['interface_clock',{label:'original-held'}]})+'\n');
    await waitFile(join(dir,'fixture-request.json'));
    input.write('{"id":2}\n{"id":3}\n');
    assert.equal(typeof busyDone,'function');assert.equal(input.isPaused(),true);
    const laterError=Error('later owned '+laterChannel+' fault');
    (laterChannel==='input'?input:output).emit('error',laterError);
    await turn();beforeRelease=settled;
  } finally {
    busyDone?.();await writeFile(join(dir,'release.json'),'{}\n',{flag:'wx'});input.end();await owner;
  }
  const start=JSON.parse(await readFile(join(dir,'fixture-start.json')));
  const end=JSON.parse(await readFile(join(dir,'fixture-exit.json')));
  const hostExit=JSON.parse(await readFile(join(dir,'host/exit.json')));
  const rows=stream.trim().split('\n').map(JSON.parse);
  const witness={started_utc:started,ended_utc:new Date().toISOString(),later_channel:laterChannel,
    before_release_settled:beforeRelease,error:{name:recordedError?.name,message:recordedError?.message,code:recordedError?.code??null},
    fixture_start:start,fixture_exit:end,host_exit:hostExit,fixture_absent:absent(start.pid),
    owned_error_listeners:{input:input.listenerCount('error'),output:output.listenerCount('error')},statuses:rows.map(row=>row.status),rows};
  await writeFile(join(dir,'WITNESS.json'),JSON.stringify(witness,null,2)+'\n',{flag:'wx'});
  await writeFile(join(dir,'output.raw.txt'),stream,{flag:'wx'});
  assert.equal(beforeRelease,false);assert.equal(end.pid,start.pid);assert.equal(end.ppid,start.ppid);
  assert.equal(end.code,0);assert.equal(end.requests,1);assert.deepEqual(hostExit,{code:0,signal:null});assert.equal(witness.fixture_absent,true);
  assert.deepEqual(witness.owned_error_listeners,{input:0,output:0});assert.deepEqual(witness.statuses,['ready','busy','returned']);
  assert.match(recordedError?.message??'',/primary busy response backlog/,'preserve the first inner diagnosis');
});
