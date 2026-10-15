import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';

const returned={result:{isError:false,content:[{type:'text',text:'{"status":"minted"}'}]}};
function setup(route='guarded-local') {
  const calls=[];
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{
    calls.push({tool,args}); return returned;
  }},route,{});
  return {calls,caller};
}

test('positional mint sends exactly the public schema and preserves original result',async()=>{
  const {calls,caller}=setup();
  assert.equal(typeof caller.mint,'function');
  const mint=caller.mint;
  assert.equal(await mint('save_fresh',27,[376,401],[24,38]),returned);
  assert.deepEqual(calls,[{tool:'interface_guarded_mint',args:{
    alias:'save_fresh',source_sequence:27,point:[376,401],region_size:[24,38]
  }}]);
  assert.equal(caller.state().stopped,null);
});

for(const [name,args] of [
  ['missing size',['save',27,[376,401]]],
  ['extra argument',['save',27,[376,401],[24,38],{}]],
  ['wrong object shape',[{alias:'save',source_sequence:27,point:[376,401],region:[24,38]}]],
  ['fractional source',['save',27.5,[376,401],[24,38]]],
  ['invalid point',['save',27,[NaN,401],[24,38]]],
  ['empty region',['save',27,[376,401],[0,38]]],
  ['too small region',['save',27,[376,401],[3,38]]],
  ['too large region',['save',27,[376,401],[24,97]]],
  ['empty alias',[' ',27,[376,401],[24,38]]]
]) test(name+' stops before any host request',async()=>{
  const {calls,caller}=setup();
  assert.equal(typeof caller.mint,'function');
  await assert.rejects(caller.mint(...args),TypeError);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.call('interface_guarded_input',{alias:'save',interaction:'click'}),/stopped/);
  assert.equal(calls.length,0);
  assert.equal(await caller.call('interface_close',{}),returned);
});

test('direct route cannot mint a guarded alias',async()=>{
  const {caller,calls}=setup('direct-post');
  assert.equal(typeof caller.mint,'function');
  await assert.rejects(caller.mint('save',27,[376,401],[24,38]),TypeError);
  assert.equal(calls.length,0);
});

test('mint after STOP does not renew a reference or dispatch',async()=>{
  const {caller,calls}=setup();
  assert.equal(typeof caller.mint,'function');
  await assert.rejects(caller.observe({target:'browser'}));
  await assert.rejects(caller.mint('save',27,[376,401],[24,38]),/stopped/);
  assert.equal(calls.length,0);
});
