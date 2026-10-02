import assert from 'node:assert/strict';
import {createPrimaryTrialCaller} from './next-primary-policy.mjs';

function setup(reply) {
  const calls=[];
  const caller=createPrimaryTrialCaller({
    async sendPresented(tool,args){calls.push({tool,args});return calls.length===1?reply:{result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'completed',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}})}]}};},
    async review(){return {};}
  },'guarded-local',{});
  return {caller,calls};
}
const refusal={result:{isError:true,content:[{type:'text',text:'expected refusal'},{type:'image',data:'refusal-image'}]}};
{
  const {caller,calls}=setup(refusal);
  assert.equal(await caller.call('interface_guarded_input',{}),refusal);
  assert.match(caller.state().stopped,/refusal/);
  await assert.rejects(caller.call('interface_guarded_input',{}),/trial stopped/);
  await caller.call('interface_close',{});
  assert.equal(calls.length,2);
}
{
  const {caller,calls}=setup({});
  await assert.rejects(caller.call('interface_guarded_input',{}));
  assert.equal(caller.state().stopped,null);
  await caller.call('interface_guarded_input',{});
  await caller.call('interface_close',{});
  assert.equal(calls.length,3);
}
process.stdout.write('construction assertions passed (2 scenarios; one expected gate failure exposed)\n');
