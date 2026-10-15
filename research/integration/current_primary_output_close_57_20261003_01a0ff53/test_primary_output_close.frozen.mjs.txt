/** Real Writable close observations; no command retry or production test hook. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {PassThrough,Writable} from 'node:stream';
import {setImmediate as tick} from 'node:timers/promises';
import {mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {servePrimaryLines} from './primary_stdio.mjs';

async function turns(){await tick();await tick();await tick();}
async function save(name,value){
  assert.ok(process.env.PRIMARY_FAILURE_EVIDENCE,'fresh explicit evidence root');
  const dir=join(process.env.PRIMARY_FAILURE_EVIDENCE,'output-close',name);
  await mkdir(dir,{recursive:true});
  await writeFile(join(dir,'WITNESS.json'),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
}
for(const kind of ['returned','busy'])test('silent close rejects '+kind+' write and retains accepted work',{timeout:5000},async()=>{
  const input=new PassThrough();let callback,release,execute=0,settlements=0,outcome='pending',failure;
  const statuses=[];let closes=0,errors=0;
  const foreignClose=()=>closes++,foreignError=()=>errors++;
  const output=new Writable({write(chunk,encoding,done){statuses.push(JSON.parse(String(chunk)).status);callback=done;}});
  output.on('close',foreignClose);output.on('error',foreignError);
  const exchange={state:()=>({next_id:execute+1}),execute:async()=>{
    execute++;if(kind==='busy')await new Promise(resolve=>release=resolve);
    return {original:true,attempt:1};
  }};
  const owner=servePrimaryLines({input,output,exchange}).then(()=>{outcome='resolved';settlements++;},error=>{outcome='rejected';failure=error;settlements++;});
  let beforeRelease,boundary,setup;
  try {
    input.write('{"id":1,"method":"call","args":[]}\n');await turns();
    if(kind==='busy'){input.write('{"id":2,"method":"call","args":[]}\n');await turns();}
    setup={callback:typeof callback,execute,statuses:[...statuses]};
    const closed=new Promise(resolve=>output.once('close',resolve));output.destroy();await closed;await turns();
    beforeRelease={outcome,settlements,execute,closes,errors};
    release?.();input.end();await turns();
    boundary={outcome,settlements,execute,closes,errors,code:failure?.code??null};
  } finally {release?.();callback?.();input.end();await owner;await turns();}
  const witness={kind,setup,before_release:beforeRelease,boundary,final:{outcome,settlements,execute,closes,errors,
    code:failure?.code??null,input_errors:input.listenerCount('error'),output_errors:output.listenerCount('error'),
    output_closes:output.listenerCount('close'),foreign_error:output.listeners('error').includes(foreignError),
    foreign_close:output.listeners('close').includes(foreignClose)},statuses};
  await save(kind,witness);
  assert.equal(setup.callback,'function');assert.equal(setup.execute,1);
  assert.equal(beforeRelease.closes,1);assert.equal(beforeRelease.errors,0);
  if(kind==='busy'){assert.equal(beforeRelease.outcome,'pending');assert.equal(beforeRelease.settlements,0);}
  assert.equal(boundary.outcome,'rejected','closed write must settle before its withheld callback is released');
  assert.equal(boundary.code,'PRIMARY_OUTPUT_CLOSED');assert.equal(boundary.execute,1);
  assert.equal(witness.final.settlements,1);assert.equal(witness.final.input_errors,0);
  assert.equal(witness.final.output_errors,1);assert.equal(witness.final.output_closes,1);
  assert.equal(witness.final.foreign_error,true);assert.equal(witness.final.foreign_close,true);
});
test('completed write remains successful after later close',async()=>{
  const input=new PassThrough();let executions=0;
  const output=new Writable({autoDestroy:false,write(chunk,encoding,done){done();}});
  const owner=servePrimaryLines({input,output,exchange:{state:()=>({next_id:2}),execute:async()=>{executions++;return {original:true};}}});
  input.end('{"id":1}\n');await owner;
  const ownedClose=output.listenerCount('close');output.destroy();await turns();
  await save('completed',{executions,owned_close_after_settlement:ownedClose,input_errors:input.listenerCount('error'),output_errors:output.listenerCount('error')});
  assert.equal(executions,1);assert.equal(ownedClose,0);assert.equal(output.listenerCount('error'),0);
});
test('callback error remains the same first object after close',async()=>{
  const input=new PassThrough();const original=Error('original callback fault');let executions=0;
  const output=new Writable({write(chunk,encoding,done){done(original);}});
  output.on('error',()=>{});let received;
  const owner=servePrimaryLines({input,output,exchange:{state:()=>({next_id:2}),execute:async()=>{executions++;return {};}}}).catch(error=>received=error);
  input.end('{"id":1}\n');await owner;await turns();
  await save('first-error',{executions,same_object:received===original,code:received?.code??null,close_listeners:output.listenerCount('close')});
  assert.equal(received,original);assert.equal(executions,1);assert.equal(output.listenerCount('close'),0);
});
test('already destroyed output rejects without another write call',async()=>{
  const input=new PassThrough();let calls=0,executions=0;
  const output=new Writable({write(chunk,encoding,done){done();}});
  const originalWrite=output.write;output.write=function(...args){calls++;return originalWrite.apply(this,args);};
  output.destroy();await turns();let received;
  const owner=servePrimaryLines({input,output,exchange:{state:()=>({next_id:2}),execute:async()=>{executions++;return {};}}}).catch(error=>received=error);
  input.end('{"id":1}\n');await owner;await turns();
  await save('preclosed',{write_calls:calls,executions,code:received?.code??null});
  assert.equal(calls,0);assert.equal(received?.code,'PRIMARY_OUTPUT_CLOSED');assert.equal(executions,1);
});
