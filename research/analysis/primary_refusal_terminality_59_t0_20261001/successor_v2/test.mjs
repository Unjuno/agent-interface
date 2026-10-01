import assert from 'node:assert/strict';
import {createPrimaryTrialCaller} from './candidate.mjs';

const good={result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'completed',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}})}]}};
const refusal={result:{isError:true,content:[{type:'text',text:'planned refusal'},{type:'image',data:'original'}]}};
async function scenario(reply,throws=false){
  const calls=[],shown=[];
  const caller=createPrimaryTrialCaller({async sendPresented(tool,args,sinks){calls.push(tool);if(calls.length===1&&throws)throw Error('send failed');const r=calls.length===1?reply:good;sinks.push(r);return r;},async review(){return {}; }},'guarded-local',shown);
  let firstError=null;try{await caller.call('interface_guarded_input',{});}catch(e){firstError=String(e);}
  return {caller,calls,shown,firstError};
}
{
 const x=await scenario(refusal);assert.match(x.caller.state().stopped,/refusal/);assert.equal(x.shown[0],refusal);
 await assert.rejects(x.caller.call('interface_guarded_input',{}),/trial stopped/);await x.caller.call('interface_close',{});
}
for(const [reply,throws] of [[{},false],[null,true]]){
 const x=await scenario(reply,throws);assert.ok(x.firstError);assert.ok(x.caller.state().stopped);
 await assert.rejects(x.caller.call('interface_guarded_input',{}),/trial stopped/);await x.caller.call('interface_close',{});
 assert.equal(x.calls.filter(t=>t==='interface_guarded_input').length,1);
}
{
 const x=await scenario(good);assert.equal(x.caller.state().stopped,null);assert.equal(x.firstError,null);
 await x.caller.call('interface_guarded_input',{});await x.caller.call('interface_close',{});
 assert.equal(x.calls.filter(t=>t==='interface_guarded_input').length,2);
}
process.stdout.write('construction PASS: refusal, malformed envelope, transport throw, valid input\n');
