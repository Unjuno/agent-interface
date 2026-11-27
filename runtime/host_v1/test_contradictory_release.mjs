import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';
for (const route of ['guarded-local','direct-post']) for (const [field,value] of [['keys_unknown',[42]],['key_state_errors',[{type:'read_error'}]],['keys_unknown','unknown'],['key_state_errors',{}]]) {
 test(`${route} rejects contradictory or malformed release ${field}`,async()=>{
  const release={verified:true,keys_down:[],buttons_down:[],[field]:value};
  const meta=route==='guarded-local'?{status:'completed',image_status:'image',result:{execution:{releases:[release]}}}:{schema:'agent-interface/review-v1',image_status:'image',receipt:{schema:'agent-interface/receipt-view-dispatch-summary-v1',execution_summary:{releases:[release]}},outcome_summary:{execution_status:'completed',input_release_verified:true,recovery_required:false,error:null}};
  const response={result:{isError:false,content:[{type:'text',text:JSON.stringify(meta)}]}};
  let calls=0;const caller=createPrimaryCaller({sendPresented:async()=>{calls++;return response;}},route,{});const tool=route==='guarded-local'?'interface_guarded_input':'interface_dispatch';
  await caller.call(tool,{interaction:'click'});assert.ok(caller.state().stopped);
  await assert.rejects(caller.call(tool,{interaction:'click'}),/stopped/);assert.equal(calls,1);
 });
}
test('empty optional diagnostics permit a verified neutral result',async()=>{
 const response={result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'completed',image_status:'image',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[],keys_unknown:[],key_state_errors:[]}]}}})}]}};
 const caller=createPrimaryCaller({sendPresented:async()=>response},'guarded-local',{});await caller.call('interface_guarded_input',{interaction:'click'});assert.equal(caller.state().stopped,null);
});
