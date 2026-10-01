import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createInstrumentedRelayClient} from './relay_host.mjs';
import {createPrimaryCaller} from './primary_caller.mjs';

// This catches the #5691 failure: extraction throws before STOP is latched.
// A synthetic host is necessary to supply an envelope a real relay rejects.
test('malformed delivered envelope prevents a second effectful host call', async () => {
  let inputs=0;
  const closed={result:{isError:false,content:[{type:'text',text:'{"status":"closed"}'}]}};
  const host={sendPresented:async tool=>{
    if(tool==='interface_close')return closed;
    inputs++; return {};
  }};
  const caller=createPrimaryCaller(host,'guarded-local',{});
  await assert.rejects(caller.call('interface_guarded_input',{alias:'field',interaction:'click'}),TypeError);
  assert.ok(caller.state().stopped,'STOP must be visible when the extraction exception reaches the primary');
  await assert.rejects(caller.call('interface_guarded_input',{alias:'field',interaction:'click'}),/stopped/);
  assert.equal(inputs,1,'catching the original error must not permit another dispatch');
  assert.equal(await caller.call('interface_close',{}),closed);
});

test('ordinary free-text MCP error returns original evidence and stops later input',async()=>{
  const response={result:{isError:true,content:[{type:'text',text:'Unknown tool'}]}};
  let calls=0;const caller=createPrimaryCaller({sendPresented:async()=>{calls++;return response;}},'direct-post',{});
  assert.equal(await caller.call('interface_dispatch',{}),response);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.call('interface_dispatch',{}),/stopped/);
  assert.equal(calls,1);
});

for (const [name,reply] of [
  ['missing text',{result:{content:[]}}],
  ['non-JSON text',{result:{content:[{type:'text',text:'not JSON'}]}}],
  ['null JSON',{result:{content:[{type:'text',text:'null'}]}}],
  ['array JSON',{result:{content:[{type:'text',text:'[]'}]}}],
]) test(name+' stops before the primary can send another call',async()=>{
  let calls=0;
  const caller=createPrimaryCaller({sendPresented:async()=>{calls++;return reply;}},'guarded-local',{});
  await assert.rejects(caller.call('interface_clock',{}));
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.call('interface_guarded_input',{alias:'x',interaction:'click'}),/stopped/);
  assert.equal(calls,1);
});

test('extraction preserves the original exception and latches before propagation',async()=>{
  const error=new TypeError('original extraction error');
  const reply={get result(){throw error;}};
  const caller=createPrimaryCaller({sendPresented:async()=>reply},'guarded-local',{});
  await assert.rejects(caller.call('interface_clock',{}),value=>value===error);
  assert.ok(caller.state().stopped);
});

test('transport rejection preserves its exception and blocks later dispatch',async()=>{
  const error=new Error('uncertain delivery');let calls=0;
  const caller=createPrimaryCaller({sendPresented:async()=>{calls++;throw error;}},'guarded-local',{});
  await assert.rejects(caller.call('interface_guarded_input',{alias:'x',interaction:'click'}),value=>value===error);
  await assert.rejects(caller.call('interface_guarded_input',{alias:'x',interaction:'click'}),/stopped/);
  assert.equal(calls,1);
});

test('fresh guarded observation uses the same no-target call as initial observation',async()=>{
  const calls=[];const response={result:{content:[{type:'text',text:'{"status":"returned"}'}]}};
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return response;}},'guarded-local',{});
  const observe=caller.observe;
  assert.equal(await observe(),response);
  assert.equal(await observe(),response);
  assert.deepEqual(calls,[{tool:'interface_guarded_observe',args:{}},{tool:'interface_guarded_observe',args:{}}]);
});

test('fresh observation rejects accidental per-call arguments before host dispatch',async()=>{
  let calls=0;const caller=createPrimaryCaller({sendPresented:async()=>{calls++;}},'guarded-local',{});
  await assert.rejects(caller.observe({target:'browser'}),/observation arguments/);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.call('interface_guarded_input',{alias:'x',interaction:'click'}),/stopped/);
  assert.equal(calls,0);
});

test('direct observation preserves the explicit snapshotted observation configuration',async()=>{
  const calls=[];const args={target:'editor',frame:'screen_physical_px',region:[0,0,800,600]};
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return {result:{content:[{type:'text',text:'{}'}]}};}},'direct-post',{},[],{observationArguments:args});
  args.target='wrong';args.region[2]=1;
  await caller.observe();
  assert.deepEqual(calls,[{tool:'interface_observe',args:{target:'editor',frame:'screen_physical_px',region:[0,0,800,600]}}]);
});

test('a completed neutral direct result returns unchanged and permits the next call',async()=>{
  const response={result:{isError:false,content:[{type:'text',text:JSON.stringify({
    schema:'agent-interface/review-v1',image_status:'image',
    receipt:{schema:'agent-interface/receipt-view-dispatch-summary-v1',execution_summary:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}},
    outcome_summary:{execution_status:'completed',input_release_verified:true,recovery_required:false,error:null}
  })},{type:'image',data:'original-image'}]}};
  let calls=0;const caller=createPrimaryCaller({sendPresented:async()=>{calls++;return response;}},'direct-post',{});
  assert.equal(await caller.call('interface_dispatch',{}),response);
  assert.equal(await caller.call('interface_dispatch',{}),response);
  assert.equal(caller.state().stopped,null);assert.equal(calls,2);
});

test('an exception during neutral-release validation blocks later input',async()=>{
  const reply={result:{content:[{type:'text',text:'{"status":"completed","image_status":"image"}'}]}};
  // A non-array releases object makes outcome validation fail.
  reply.result.content[0].text='{"status":"completed","image_status":"image","result":{"execution":{"releases":{"length":1}}}}';
  const caller=createPrimaryCaller({sendPresented:async()=>reply},'guarded-local',{});
  await assert.rejects(caller.call('interface_guarded_input',{alias:'x',interaction:'click'}),TypeError);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.call('interface_guarded_input',{alias:'x',interaction:'click'}),/stopped/);
});

test('real host text-only declared refusal is presented and acknowledged without stopping',async()=>{
  const directory=join(await mkdtemp(join(tmpdir(),'primary-caller-text-')),'host');
  const fixture="require('node:readline').createInterface({input:process.stdin}).on('line',line=>{const r=JSON.parse(line); console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{isError:true,content:[{type:'text',text:JSON.stringify({status:'refused',replay_allowed:false,error:'KeyError(4)',input_dispatched:false,session:{binding_revision:1,recovery_required:false}})}]}}));});";
  const host=await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory:directory});
  const args={alias:'old',source_sequence:4,point:[230,401],region_size:[24,38]};
  const seen=[];const caller=createPrimaryCaller(host,'guarded-local',{text:value=>seen.push(value),image:()=>assert.fail('unexpected image')},[{id:'revoked',tool:'interface_guarded_mint',args,kind:'source',error:'KeyError(4)',revision:1}]);
  try {
    const response=await caller.call('interface_guarded_mint',args,'revoked');
    assert.equal(response.result.isError,true);assert.equal(caller.state().stopped,null);
    assert.ok(seen.some(value=>typeof value==='string'&&value.includes('KeyError(4)')));
    await caller.acknowledgeText(response.attempt,{task:'test',phase:'refusal',reason:'Read original no-input KeyError'});
    const ack=JSON.parse(await readFile(join(directory,'text-acknowledgment-1.json'),'utf8'));
    assert.equal(ack.isError,true);
    await assert.rejects(caller.call('interface_guarded_mint',args,'revoked'),/consumed/);
    assert.equal(host.state().attempts,1);
  } finally {await host.close();}
});

for (const cue of ['matched','pending','rejected','needs_review'])
  test('explicit input feedback '+cue+' retains evidence and enforces STOP',async()=>{
    const meta={status:cue==='matched'?'completed':'needs_review',
      image_status:'image',task_success:null,replay_allowed:false,
      feedback:{status:cue},result:{status:'completed',execution:{releases:[
        {verified:true,keys_down:[],buttons_down:[]}]}}};
    const reply={result:{isError:cue!=='matched',content:[
      {type:'text',text:JSON.stringify(meta)},{type:'image',data:'original-cue'}]}};
    const calls=[];const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{
      calls.push({tool,args});return reply;}},'guarded-local',{});
    const args={alias:'save',offset:[12,12],tail:[],feedback:{expected_title:'saved',timeout_ms:1000}};
    assert.equal(await caller.call('interface_guarded_input',args),reply);
    assert.deepEqual(calls[0].args,args);
    if(cue==='matched')assert.equal(caller.state().stopped,null);
    else {
      assert.ok(caller.state().stopped);
      await assert.rejects(caller.observe(),/stopped/);
      assert.equal(calls.length,1);
      assert.equal(await caller.call('interface_close',{}),reply);
      assert.equal(calls.length,2);
    }
  });
