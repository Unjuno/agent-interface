import {createPrimaryTrialCaller} from './next-primary-policy.mjs';

const success = {result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'completed',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}})}]}};
function fixture(firstReply) {
  const calls = [];
  const presented = [];
  const host = {
    async sendPresented(tool, args, sinks) {
      calls.push({tool, args});
      const reply = calls.length === 1 ? firstReply : success;
      sinks.push(reply);
      return reply;
    },
    async review() { throw Error('unused'); }
  };
  return {caller:createPrimaryTrialCaller(host, 'guarded-local', presented), calls, presented};
}

async function scenario(caseId, reply) {
  const {caller, calls, presented} = fixture(reply);
  let firstError = null;
  try { await caller.call('interface_guarded_input', {caseId:'first'}); }
  catch (error) { firstError = String(error); }
  let second;
  try {
    second = {status:'returned', value:await caller.call('interface_guarded_input', {caseId:'after-fault'})};
  } catch (error) { second = {status:'blocked', error:String(error)}; }
  let close;
  try { await caller.call('interface_close', {caseId}); close = 'allowed'; }
  catch (error) { close = 'blocked:' + String(error); }
  return {case_id:caseId, first_error:firstError, second, close,
    caller_state:caller.state(), host_calls:calls.map(c=>({tool:c.tool, args:c.args})),
    host_call_count:calls.length, presented_count:presented.length,
    original_reply_preserved:presented[0]===reply};
}

const refusal = {result:{isError:true,content:[
  {type:'text',text:'planned guard refusal'}, {type:'image',data:'original-refusal-image'}
]}};
const malformed = {};
const rows = [
  await scenario('explicit_planned_refusal', refusal),
  await scenario('invalid_envelope_uncertain_delivery', malformed)
];
process.stdout.write(JSON.stringify({schema:'issue59-refusal-terminality-t0-v1',rows})+'\n');
