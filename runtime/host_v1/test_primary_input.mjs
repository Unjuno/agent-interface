import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';

const returned={result:{isError:false,content:[{type:'text',text:JSON.stringify({
  status:'completed',image_status:'image',result:{execution:{releases:[
    {verified:true,keys_down:[],buttons_down:[]}
  ]}}
})}]}};
function setup(route='guarded-local') {
  const calls=[];
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{
    calls.push({tool,args}); return returned;
  }},route,{});
  return {caller,calls};
}
test('explicit positional input preserves offset, tail, and original response',async()=>{
  const {caller,calls}=setup();
  assert.equal(typeof caller.input,'function');
  const input=caller.input;
  const tail=[{op:'text',text:'t1001059-4'}];
  assert.equal(await input('field_b',[12,19],'click',tail),returned);
  assert.deepEqual(calls,[{tool:'interface_guarded_input',args:{
    alias:'field_b',offset:[12,19],interaction:'click',tail,
    detail:'brief',observation_refs:true
  }}]);
  assert.equal(caller.state().stopped,null);
});
for(const [name,args] of [
  ['missing offset',['field_b']],
  ['object instead of positional arguments',[{alias:'field_b',interaction:'click',tail:[]}]],
  ['fractional offset',['field_b',[12.5,19],'click',[]]],
  ['missing tail',['field_b',[12,19],'click']],
  ['invalid interaction',['field_b',[12,19],'focus',[]]],
  ['extra argument',['field_b',[12,19],'click',[],{}]]
]) test(name+' fails before dispatch and prevents corrected replay',async()=>{
  const {caller,calls}=setup();
  assert.equal(typeof caller.input,'function');
  await assert.rejects(caller.input(...args),TypeError);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.input('field_b',[12,19],'click',[]),/stopped/);
  assert.equal(calls.length,0);
  await caller.call('interface_close',{});
  assert.equal(calls.length,1);
});
test('direct caller cannot dispatch guarded positional input',async()=>{
  const {caller,calls}=setup('direct-post');
  assert.equal(typeof caller.input,'function');
  await assert.rejects(caller.input('field_b',[12,19],'click',[]),TypeError);
  assert.equal(calls.length,0);
});
test('uncloneable tail stops before dispatch and cannot be retried',async()=>{
  const {caller,calls}=setup();
  await assert.rejects(caller.input('field_b',[12,19],'click',[{op:'text',text:()=>{}}]));
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.input('field_b',[12,19],'click',[]),/stopped/);
  assert.equal(calls.length,0);
});
