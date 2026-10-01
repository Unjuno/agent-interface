import {createPrimaryTrialCaller} from './candidate.mjs';

const good={result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'completed',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}})}]}};
const refusal={result:{isError:true,content:[{type:'text',text:'planned refusal'},{type:'image',data:'original-refusal-image'}]}};

async function execute(caseId, firstReply, throwsFirst=false) {
  const calls=[], presented=[];
  const host={async sendPresented(tool,args,sinks){
    calls.push({tool,args});
    if(calls.length===1 && throwsFirst) throw Error('presentation transport failed');
    const reply=calls.length===1?firstReply:good;
    sinks.push(reply);
    return reply;
  },async review(){return {};}};
  const caller=createPrimaryTrialCaller(host,'guarded-local',presented);
  let first;
  try { first={status:'returned',value:await caller.call('interface_guarded_input',{caseId:'first'})}; }
  catch(e) { first={status:'threw',error:String(e)}; }
  let next;
  try { next={status:'returned',value:await caller.call('interface_guarded_input',{caseId:'after-fault'})}; }
  catch(e) { next={status:'blocked',error:String(e)}; }
  let close;
  try { await caller.call('interface_close',{caseId}); close='allowed'; }
  catch(e) { close='blocked:'+String(e); }
  return {case_id:caseId,first,next,close,stopped:caller.state().stopped,
    calls,presented_count:presented.length,first_reply_to_presentation:presented[0]??null,
    original_refusal_image_preserved:presented[0]?.result?.content?.some(c=>c.type==='image'&&c.data==='original-refusal-image')??false};
}

const rows=[
  await execute('explicit_refusal',refusal),
  await execute('malformed_envelope',{}),
  await execute('valid_input',good),
  await execute('transport_throw',null,true)
];
for(const row of rows) process.stdout.write(JSON.stringify(row)+'\n');
