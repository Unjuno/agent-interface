import test from 'node:test';
import assert from 'node:assert/strict';
import {appendFileSync} from 'node:fs';
import {createPrimaryCaller} from './primary_caller.mjs';

const shapes=['healthy-array','object-length-one','object-length-extra','empty-array','double-array','wrong-stage','wrong-status','wrong-reason','wrong-handle'];
for(const route of ['guarded-local','direct-post'])for(const shape of shapes)
test('primary control container '+route+' '+shape,async()=>{
 const tool=route==='guarded-local'?'interface_guarded_input':'interface_dispatch';
 const args={alias:'stale_v3',interaction:'click'};
 const guard={stage:'before_admission',status:'MISSING',reason:'new-guard-missing',handle:'stale_v3'};
 let checks=[guard];
 if(shape==='object-length-one')checks={0:guard,length:1};
 else if(shape==='object-length-extra')checks={0:guard,length:1,extra:'not-an-array'};
 else if(shape==='empty-array')checks=[];
 else if(shape==='double-array')checks=[guard,guard];
 else if(shape.startsWith('wrong-'))guard[shape.slice(6)]='different';
 const meta={status:'refused',replay_allowed:false,session:{binding_revision:9,recovery_required:false},result:{input_dispatched:false,execution:null,guard_checks:checks}};
 const original={attempt:1,result:{isError:true,content:[{type:'text',text:JSON.stringify(meta)},{type:'image',mimeType:'image/png',data:'AAECAw=='}]}};
 const clock={attempt:2,result:{isError:false,content:[{type:'text',text:'{"status":"returned"}'}]}};
 const closed={result:{isError:false,content:[{type:'text',text:'{"status":"closed"}'}]}};
 const calls=[],shown=[];
 const host={sendPresented:async(t,a,sinks)=>{
  calls.push({tool:t,args:structuredClone(a)});
  const reply=t==='interface_close'?closed:t==='interface_clock'?clock:original;
  for(const block of reply.result.content)if(block.type==='text')await sinks.text(block.text);else await sinks.image(block);
  return reply;
 }};
 const caller=createPrimaryCaller(host,route,{text:value=>shown.push({kind:'text',value}),image:value=>shown.push({kind:'image',value})},[{id:'new-control',tool,args,kind:'post',revision:9,reason:'new-guard-missing',alias:'stale_v3'}]);
 const row={route,shape,original,physical_inputs:0};let failure=null;
 try {
  row.original_returned=(await caller.call(tool,args,'new-control'))===original;
  row.first_stop=caller.state().stopped;row.first_shown=structuredClone(shown);row.first_calls=structuredClone(calls);
  assert.equal(row.original_returned,true);
  assert.deepEqual(row.first_shown,[{kind:'text',value:original.result.content[0].text},{kind:'image',value:original.result.content[1]}]);
  assert.deepEqual(calls,[{tool,args}]);
  if(shape==='healthy-array'){
   assert.equal(row.first_stop,null);assert.equal(await caller.call('interface_clock',{}),clock);
   await assert.rejects(caller.call(tool,args,'new-control'),/consumed/);assert.equal(calls.length,2);
  }else{
   assert.equal(row.first_stop,'control outcome mismatch');await assert.rejects(caller.call('interface_clock',{}),/stopped/);
   await assert.rejects(caller.call(tool,args,'new-control'),/stopped/);assert.equal(calls.length,1);
  }
  row.stop_before_close=caller.state().stopped;
  assert.equal(await caller.call('interface_close',{}),closed);assert.equal(caller.state().stopped,row.stop_before_close);
  row.assertions_passed=true;
 }catch(error){row.assertions_passed=false;failure=error;row.assertion_error={name:error.name,message:error.message};throw error;}
 finally{
  row.final_stop=caller.state().stopped;row.calls=structuredClone(calls);row.shown=structuredClone(shown);
  if(process.env.TASK_PRIMARY_CONTROL_TRACE)appendFileSync(process.env.TASK_PRIMARY_CONTROL_TRACE,JSON.stringify(row)+'\n');
 }
});
