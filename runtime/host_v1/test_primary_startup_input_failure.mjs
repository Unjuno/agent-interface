import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

test('an input error during exchange creation is owned before readiness',()=>{
  const fixture=[
    "const fs=require('node:fs');let bytes=0;",
    "fs.writeFileSync(process.argv[1],JSON.stringify({pid:process.pid,ppid:process.ppid})+'\\n',{flag:'wx'});",
    "process.stdin.on('data',chunk=>{bytes+=chunk.length;});",
    "process.on('exit',code=>fs.writeFileSync(process.argv[2],JSON.stringify({pid:process.pid,code,bytes})+'\\n',{flag:'wx'}));",
    'process.stdin.resume();',
  ].join('\n');
  const source=`(async()=>{
    const fsp=require('node:fs/promises');
    const {syncBuiltinESMExports}=require('node:module');
    const {PassThrough}=require('node:stream');
    const {mkdtemp,readFile}=require('node:fs/promises');
    const {tmpdir}=require('node:os');const {join,resolve}=require('node:path');
    const {runPrimaryStdio}=await import('./runtime/host_v1/primary_stdio.mjs');
    const root=await mkdtemp(join(tmpdir(),'primary-startup-async-error-'));
    const input=new PassThrough(),output=new PassThrough(),statuses=[];
    output.on('data',chunk=>statuses.push(JSON.parse(chunk.toString()).status));
    const fault=Error('asynchronous input failure during exchange creation');
    const originalMkdir=fsp.mkdir;
    fsp.mkdir=async(...args)=>{
      const result=await originalMkdir(...args);
      if(resolve(args[0])===join(root,'exchange')){
        await new Promise(resolve=>setImmediate(()=>{input.emit('error',fault);resolve();}));
      }
      return result;
    };
    syncBuiltinESMExports();
    const config={host:{command:process.execPath,args:['-e',${JSON.stringify(fixture)},join(root,'fixture-start.json'),join(root,'fixture-exit.json')],evidenceDirectory:join(root,'host')},route:'guarded-local',exchangeDirectory:join(root,'exchange')};
    let observed=false;
    try {await runPrimaryStdio(config,{input,output});}
    catch(error){if(error!==fault)throw error;observed=true;}
    finally {fsp.mkdir=originalMkdir;syncBuiltinESMExports();}
    const hostExit=JSON.parse(await readFile(join(root,'host/exit.json')));
    const fixtureStart=JSON.parse(await readFile(join(root,'fixture-start.json')));
    const fixtureExit=JSON.parse(await readFile(join(root,'fixture-exit.json')));
    let childAbsent=false;try {process.kill(fixtureStart.pid,0);}catch(error){if(error.code==='ESRCH')childAbsent=true;else throw error;}
    console.log(JSON.stringify({observed,statuses,hostExit,fixtureStart,fixtureExit,childAbsent,listeners:{input:input.listenerCount('error'),output:output.listenerCount('error')}}));
  })().catch(error=>{console.error(String(error));process.exitCode=3;});`;
  const child=spawnSync(process.execPath,['--eval',source],{
    cwd:fileURLToPath(new URL('../../',import.meta.url)),encoding:'utf8',timeout:5000
  });
  assert.equal(child.status,0,child.stderr||String(child.error));
  const result=JSON.parse(child.stdout.trim());
  assert.equal(result.observed,true);
  assert.deepEqual(result.statuses,[]);
  assert.deepEqual(result.hostExit,{code:0,signal:null});
  assert.equal(result.fixtureExit.code,0);
  assert.equal(result.fixtureExit.bytes,0);
  assert.equal(result.fixtureStart.pid,result.fixtureExit.pid);
  assert.equal(result.childAbsent,true);
  assert.deepEqual(result.listeners,{input:0,output:0});
});
