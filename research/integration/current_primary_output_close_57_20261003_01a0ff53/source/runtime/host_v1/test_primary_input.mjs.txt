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

test('explicit inputWithFeedback snapshots the policy and retains original reply',async()=>{
  const calls=[];const reply={result:{isError:false,content:[{type:'text',text:JSON.stringify({
    status:'completed',image_status:'image',task_success:null,
    feedback:{status:'matched',expected_title:'saved',rejected_titles:['failed'],title:'saved',after_title:'saved',task_success:null,authority_granted:false,input_dispatched:false},
    result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}
  })}]}};
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return reply;}},'guarded-local',{});
  const policy={expected_title:'saved',rejected_titles:['failed'],timeout_ms:1000};
  const tail=[{op:'wait_update',milliseconds:50}];const input=caller.inputWithFeedback;
  assert.equal(typeof input,'function');const pending=input('save',[12,12],'click',tail,policy);
  policy.expected_title='other';policy.rejected_titles.push('other');tail[0].milliseconds=999;
  assert.equal(await pending,reply);assert.equal(caller.state().stopped,null);
  assert.deepEqual(calls,[{tool:'interface_guarded_input',args:{alias:'save',offset:[12,12],interaction:'click',tail:[{op:'wait_update',milliseconds:50}],detail:'brief',observation_refs:true,feedback:{expected_title:'saved',rejected_titles:['failed'],timeout_ms:1000}}}]);
});
for(const policy of [null,{}, {expected_title:''},{expected_title:'saved',timeout_ms:10001},
  {expected_title:'saved',timeout_ms:1.5},{expected_title:'saved',rejected_titles:['saved']},
  {expected_title:'saved',rejected_titles:[null]},{expected_title:'saved',extra:true}])
  test('invalid explicit feedback '+JSON.stringify(policy)+' stops before host dispatch',async()=>{
    const {caller,calls}=setup();assert.equal(typeof caller.inputWithFeedback,'function');
    await assert.rejects(caller.inputWithFeedback('save',[12,12],'click',[],policy),TypeError);
    assert.ok(caller.state().stopped);assert.equal(calls.length,0);
    await assert.rejects(caller.input('save',[12,12],'click',[]),/stopped/);
  });
test('missing requested cue cannot pass through a completed input reply',async()=>{
  const {caller,calls}=setup();
  assert.equal(await caller.call('interface_guarded_input',{alias:'save',offset:[12,12],tail:[],feedback:{expected_title:'saved'}}),returned);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.observe(),/stopped/);assert.equal(calls.length,1);
});

for(const change of ['title','after_title','expected_title','rejected_titles','authority_granted','input_dispatched','task_success'])
  test('inconsistent requested cue '+change+' preserves reply and stops next input',async()=>{
    const cue={status:'matched',expected_title:'saved',rejected_titles:[],title:'saved',after_title:'saved',task_success:null,authority_granted:false,input_dispatched:false};
    cue[change]=change==='rejected_titles'?['other']:change==='task_success'?true:change.endsWith('granted')||change==='input_dispatched'?true:'wrong';
    const response=structuredClone(returned);response.result.content[0].text=JSON.stringify({status:'completed',image_status:'image',feedback:cue,result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}});
    let calls=0;const caller=createPrimaryCaller({sendPresented:async()=>{calls++;return response;}},'guarded-local',{});
    assert.equal(await caller.inputWithFeedback('save',[12,12],'click',[],{expected_title:'saved'}),response);
    assert.ok(caller.state().stopped);await assert.rejects(caller.input('save',[12,12],'click',[]),/stopped/);assert.equal(calls,1);
  });
test('uncloneable feedback policy stops before dispatch',async()=>{
  const {caller,calls}=setup();await assert.rejects(caller.inputWithFeedback('save',[12,12],'click',[],{expected_title:'saved',extra:()=>{}}));
  assert.ok(caller.state().stopped);assert.equal(calls.length,0);
});
