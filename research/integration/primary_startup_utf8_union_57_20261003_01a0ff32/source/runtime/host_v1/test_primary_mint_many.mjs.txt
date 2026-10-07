import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';

const references=[{alias:'field',point:[230,401],region_size:[24,38]},
  {alias:'save',point:[376,401],region_size:[24,14]}];
function setup(meta={status:'minted',source_sequence:7,minted:[{alias:'field'},{alias:'save'}]},route='guarded-local') {
  const calls=[];
  const reply={result:{isError:false,content:[{type:'text',text:JSON.stringify(meta)}]}};
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return reply;}},route,{});
  return {caller,calls,reply};
}

test('mintMany sends one public request with a copied explicit same-source batch',async()=>{
  const {caller,calls,reply}=setup();
  const refs=structuredClone(references),mintMany=caller.mintMany;
  assert.equal(typeof mintMany,'function');
  const pending=mintMany(7,refs);refs[0].point[0]=999;refs.push(references[0]);
  assert.equal(await pending,reply);
  assert.deepEqual(calls,[{tool:'interface_guarded_mint_many',args:{source_sequence:7,references}}]);
  assert.equal(caller.state().stopped,null);
});

for (const [name,args] of [
  ['duplicate alias',[7,[references[0],references[0]]]],
  ['extra argument',[7,references,{}]],
  ['empty batch',[7,[]]],
  ['over capacity',[7,Array.from({length:9},(_,i)=>({...references[0],alias:'a'+i}))]],
  ['bad alias',[7,[{...references[0],alias:'Field'}]]],
  ['unknown property',[7,[{...references[0],region:[24,38]}]]],
  ['fractional source',[7.5,references]],
  ['fractional point',[7,[{...references[0],point:[1.5,2]}]]],
  ['hole in point',[7,[{...references[0],point:[,2]}]]],
  ['hole in batch',[7,Array(2)]],
  ['out of range size',[7,[{...references[0],region_size:[24,97]}]]]
]) test(name+' stops before registration and subsequent input',async()=>{
  const {caller,calls,reply}=setup();
  assert.equal(typeof caller.mintMany,'function');
  await assert.rejects(caller.mintMany(...args),TypeError);
  await assert.rejects(caller.input('field',[12,19],'click',[]),/stopped/);
  assert.equal(calls.length,0);
  assert.equal(await caller.call('interface_close',{}),reply);
});

for (const [name,meta] of [
  ['partial registration',{status:'mint_incomplete',source_sequence:7,minted:[{alias:'field'}],failed_alias:'save',failed_alias_state:'unknown'}],
  ['missing reference',{status:'minted',source_sequence:7,minted:[{alias:'field'}]}],
  ['wrong source',{status:'minted',source_sequence:8,minted:[{alias:'field'},{alias:'save'}]}],
  ['wrong order',{status:'minted',source_sequence:7,minted:[{alias:'save'},{alias:'field'}]}]
]) test(name+' returns original evidence and latches STOP without replay',async()=>{
  const {caller,calls,reply}=setup(meta);
  assert.equal(typeof caller.mintMany,'function');
  assert.equal(await caller.mintMany(7,references),reply);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.mintMany(7,references),/stopped/);
  assert.equal(calls.length,1);
  assert.equal(await caller.call('interface_close',{}),reply);
});

test('direct route cannot register guarded references',async()=>{
  const {caller,calls}=setup(undefined,'direct');
  assert.equal(typeof caller.mintMany,'function');
  await assert.rejects(caller.mintMany(7,references),TypeError);
  assert.equal(calls.length,0);
});

test('raw batch call also refuses to continue after uncertain partial registration',async()=>{
  const {caller,calls,reply}=setup({status:'mint_incomplete',minted:[],failed_alias_state:'unknown'});
  assert.equal(await caller.call('interface_guarded_mint_many',{source_sequence:7,references}),reply);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.input('field',[12,19],'click',[]),/stopped/);
  assert.equal(calls.length,1);
});
