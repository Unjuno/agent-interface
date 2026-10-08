/* Literal byte-admission regressions; synthetic exchange has no backend authority. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {PassThrough,Readable} from 'node:stream';
import {servePrimaryLines} from './primary_stdio.mjs';
const prefix=Buffer.from('{"id":1,"method":"call","args":["interface_clock",{"label":"');
const suffix=Buffer.from('"}]}\n');
const command=bytes=>Buffer.concat([prefix,bytes,suffix]);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function run(chunks,{strings=false,foreign=false}={}){
 const input=strings?Readable.from(chunks):new PassThrough(),output=new PassThrough();
 const calls=[],written=[];let next=1,error=null;
 const observer=()=>{};
 if(foreign){input.on('end',observer);input.on('error',observer);output.on('error',observer);}
 output.on('data',b=>written.push(Buffer.from(b)));
 const exchange={state:()=>({next_id:next}),execute:async value=>{calls.push(structuredClone(value));next++;return {value,next_id:next};}};
 const pending=servePrimaryLines({exchange,input,output});pending.catch(()=>{});
 if(!strings){for(const chunk of chunks){input.write(chunk);await tick();}input.end();}
 try{await pending;}catch(e){error=e;}
 const rows=Buffer.concat(written).toString('utf8').split('\n').filter(Boolean).map(JSON.parse);
 return {calls,next,error,rows,input,output,observer};
}
for(const [name,bytes] of [['illegal-ff',[255]],['incomplete-e3-in-string',[227]],['lone-continuation',[128]],['overlong-slash',[192,175]],['utf8-surrogate',[237,160,128]]]){
 test(name,{timeout:3000},async()=>{
  const r=await run([command(Buffer.from(bytes))]);
  assert.ok(r.error instanceof TypeError,'malformed byte stream must terminate before exchange');
  assert.equal(r.calls.length,0);assert.equal(r.next,1);assert.deepEqual(r.rows,[]);
 });
}
test('incomplete-byte-at-EOF',{timeout:3000},async()=>{
 const r=await run([Buffer.concat([prefix,Buffer.from([227])])]);
 assert.ok(r.error instanceof TypeError);assert.equal(r.calls.length,0);assert.equal(r.next,1);
});
test('ordinary-ascii-is-unchanged',async()=>{
 const r=await run([command(Buffer.from('plain'))]);assert.equal(r.error,null);
 assert.equal(r.calls[0].args[1].label,'plain');assert.equal(r.next,2);assert.equal(r.rows[0].status,'returned');
});
test('split-valid-multibyte-survives-byte-boundaries',async()=>{
 const r=await run([Buffer.concat([prefix,Buffer.from([227])]),Buffer.from([129]),Buffer.concat([Buffer.from([130]),suffix])]);
 assert.equal(r.error,null);assert.equal(r.calls.length,1);assert.equal(r.calls[0].args[1].label,'あ');assert.equal(r.next,2);
});
test('literal-replacement-character-is-valid',async()=>{
 const r=await run([command(Buffer.from('�'))]);assert.equal(r.error,null);assert.equal(r.calls[0].args[1].label,'�');assert.equal(r.next,2);
});
test('already-decoded-text-caller-is-preserved',async()=>{
 const r=await run([command(Buffer.from('あ')).toString('utf8')],{strings:true});
 assert.equal(r.error,null);assert.equal(r.calls[0].args[1].label,'あ');assert.equal(r.next,2);
});
test('existing-malformed-JSON-is-refused-without-consuming',async()=>{
 const r=await run([Buffer.from('{"id":}\n')]);assert.equal(r.error,null);assert.equal(r.calls.length,0);assert.equal(r.next,1);
 assert.equal(r.rows[0].status,'refused');assert.equal(r.rows[0].operation_invoked,false);assert.equal(r.rows[0].next_id,1);
});
test('accepted-same-promise-finishes-before-malformed-byte-rejection',{timeout:3000},async()=>{
 const input=new PassThrough(),output=new PassThrough();const calls=[],written=[];let next=1,settled=false,error=null;
 let entered,release;const inside=new Promise(r=>entered=r),held=new Promise(r=>release=r);
 output.on('data',b=>written.push(Buffer.from(b)));
 const exchange={state:()=>({next_id:next}),execute:async c=>{calls.push(c);next++;entered();await held;return {original:true,next_id:next};}};
 const pending=servePrimaryLines({exchange,input,output}).then(()=>{settled=true;},e=>{settled=true;error=e;});
 input.write(command(Buffer.from('accepted')));await inside;
 input.write(command(Buffer.from([255])));input.end();await tick();const before=settled;
 release();await pending;
 assert.equal(before,false,'keep observing the already accepted original work');
 assert.ok(error instanceof TypeError);assert.equal(calls.length,1);assert.equal(next,2);
 assert.deepEqual(Buffer.concat(written).toString('utf8').trim().split('\n').map(JSON.parse).map(x=>x.status),['returned']);
});
test('unaccepted-valid-prefix-in-corrupted-chunk-is-refused',async()=>{
 const r=await run([Buffer.concat([command(Buffer.from('unaccepted')),command(Buffer.from([255]))])]);
 assert.ok(r.error instanceof TypeError);assert.equal(r.calls.length,0);assert.equal(r.next,1);
});
test('existing-BOM-JSON-refusal-is-preserved',async()=>{
 const r=await run([Buffer.concat([Buffer.from([239,187,191]),command(Buffer.from('plain'))])]);
 assert.equal(r.error,null);assert.equal(r.calls.length,0);assert.equal(r.next,1);assert.equal(r.rows[0].status,'refused');
});
test('owned-validation-listeners-retire-and-foreign-observers-stay',async()=>{
 const r=await run([command(Buffer.from('plain'))],{foreign:true});assert.equal(r.error,null);
 assert.equal(r.input.listenerCount('data'),0);assert.deepEqual(r.input.listeners('end'),[r.observer]);
 assert.deepEqual(r.input.listeners('error'),[r.observer]);assert.deepEqual(r.output.listeners('error'),[r.observer]);
});
