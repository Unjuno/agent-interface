import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';

for(const kind of ['mint','feedback'])test('raw '+kind+' validates the admitted snapshot after a callback mutation',async()=>{
  const args=kind==='mint'?{source_sequence:1,references:[{alias:'field'}]}:{feedback:{expected_title:'saved',rejected_titles:[]}};
  let calls=0,seen;
  const host={sendPresented:async(tool,admitted)=>{
    calls++;seen=structuredClone(admitted);
    if(kind==='mint')args.references[0].alias='changed';else args.feedback.expected_title='changed';
    const meta=kind==='mint'?{status:'minted',source_sequence:seen.source_sequence,minted:[{alias:seen.references[0].alias}]}:
      {status:'completed',image_status:'image',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}},
        feedback:{status:'matched',expected_title:seen.feedback.expected_title,rejected_titles:[],title:seen.feedback.expected_title,after_title:seen.feedback.expected_title,task_success:null,authority_granted:false,input_dispatched:false}};
    return {result:{isError:false,content:[{type:'text',text:JSON.stringify(meta)}]}};
  }};
  const caller=createPrimaryCaller(host,'guarded-local',{});
  const reply=await caller.call(kind==='mint'?'interface_guarded_mint_many':'interface_guarded_input',args);
  assert.equal(caller.state().stopped,null);assert.equal(calls,1);assert.notEqual(seen,args);assert.equal(reply.result.isError,false);
});

test('uncloneable arguments stop before host dispatch and preserve the clone error',async()=>{
  let calls=0;const caller=createPrimaryCaller({sendPresented:()=>{calls++;}},'guarded-local',{});
  await assert.rejects(caller.call('interface_clock',{uncloneable:()=>{}}),{name:'DataCloneError'});
  assert.equal(calls,0);assert.equal(caller.state().stopped,'primary request snapshot failure');
  await assert.rejects(caller.call('interface_clock',{}),/trial stopped/);assert.equal(calls,0);
});

test('unavailable tools reject before reading or cloning arguments',async()=>{
  let reads=0,calls=0;const caller=createPrimaryCaller({sendPresented:()=>{calls++;}},'guarded-local',{});
  await assert.rejects(caller.call('not_available',{get x(){reads++;throw Error('must not read');}}),/unavailable tool/);
  assert.equal(reads,0);assert.equal(calls,0);
});

test('snapshot preserves strict control admission and original returned evidence',async()=>{
  const args={source_sequence:1,references:[{alias:'field'}]};let calls=0;
  const original={result:{isError:true,content:[{type:'text',text:JSON.stringify({status:'refused',replay_allowed:false,error:'missing source',input_dispatched:false,session:{binding_revision:2,recovery_required:false}})}]}};
  const caller=createPrimaryCaller({sendPresented:async()=>{calls++;return original;}},'guarded-local',{},[{id:'negative',tool:'interface_guarded_mint_many',args,kind:'source',revision:2,error:'missing source'}]);
  assert.equal(await caller.call('interface_guarded_mint_many',args,'negative'),original);assert.equal(caller.state().stopped,null);
  await assert.rejects(caller.call('interface_guarded_mint_many',args,'negative'),/consumed/);assert.equal(calls,1);
});
