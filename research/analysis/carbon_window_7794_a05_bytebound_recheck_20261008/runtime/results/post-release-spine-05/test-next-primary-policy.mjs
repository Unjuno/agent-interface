import assert from 'node:assert/strict';
import {createPrimaryTrialCaller} from './next-primary-policy.mjs';

function setup(reply) {
  const calls=[], reviews=[];
  const host={sendPresented:async(tool,args)=>{calls.push({tool,args});return reply;},
    review:async(attempt,review)=>{reviews.push({attempt,review});return review;}};
  return {caller:createPrimaryTrialCaller(host,'guarded-local',{}),calls,reviews};
}
const success={result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'completed',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}})},{type:'image',data:'original'}]}};
{
  const {caller,calls}=setup(success);
  await assert.rejects(caller.call('interface_observe',{}),/unavailable tool/);
  assert.equal(calls.length,0);
  await assert.rejects(caller.call('interface_guarded_input',{}),/trial stopped/);
  await caller.call('interface_close',{});assert.equal(calls.length,1);
}
{
  const {caller,reviews,calls}=setup(success);
  await assert.rejects(caller.review(4,{phase:'initial',reason:'seen'}),/invalid primary review/);
  assert.equal(reviews.length,0);assert.equal(calls.length,0);
  await caller.call('interface_close',{});assert.equal(calls[0].tool,'interface_close');
}
for(const bad of [
  {result:{isError:true,content:[{type:'text',text:'Unknown tool'},{type:'image',data:'original'}]}},
  {result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'execution_failed'})}]}},
  {result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'completed',result:{execution:{releases:[{verified:true,keys_down:['CTRL'],buttons_down:[]}]}}})}]}}
]) {
  const {caller,calls}=setup(bad);
  assert.equal(await caller.call('interface_guarded_input',{}),bad);
  await assert.rejects(caller.call('interface_guarded_input',{}),/trial stopped/);
  assert.equal(calls.length,1);
  await caller.call('interface_close',{});assert.equal(calls.length,2);
}
{
  const {caller,reviews}=setup(success);
  assert.equal(await caller.call('interface_guarded_input',{}),success);
  await caller.review(1,{task:'task-1',phase:'saved',reason:'Primary viewed original.'});
  assert.equal(reviews.length,1);assert.equal(caller.state().stopped,null);
}
console.log('PASS: wrong tool, missing review argument, original error delivery, incomplete input, held input, neutral success and close after STOP');
