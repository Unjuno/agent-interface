import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
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

test('explicit observation budget covers helper and raw tool calls before dispatch',async()=>{
  const calls=[];
  const response={result:{content:[{type:'text',text:'{"status":"returned"}'}]}};
  const closed={result:{content:[{type:'text',text:'{"status":"closed"}'}]}};
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{
    calls.push({tool,args});return tool==='interface_close'?closed:response;
  }},'guarded-local',{},[],{maxExplicitObservations:1});
  assert.equal(await caller.observe(),response);
  await assert.rejects(caller.call('interface_guarded_observe',{}),/observation budget exhausted/);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.input('field',[0,0],'click',[]),/stopped/);
  assert.equal(await caller.call('interface_close',{}),closed);
  assert.deepEqual(calls,[
    {tool:'interface_guarded_observe',args:{}},
    {tool:'interface_close',args:{}}
  ]);
});

test('zero observation budget refuses first direct capture before host dispatch',async()=>{
  const calls=[];
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{
    calls.push({tool,args});return {result:{content:[{type:'text',text:'{}'}]}};
  }},'direct-post',{},[],{observationArguments:{target:'editor'},maxExplicitObservations:0});
  await assert.rejects(caller.observe(),/observation budget exhausted/);
  assert.ok(caller.state().stopped);
  assert.deepEqual(calls,[]);
});

for(const value of [-1,1.5,Number.MAX_SAFE_INTEGER+1,null])
  test('invalid explicit observation budget '+String(value)+' is rejected at construction',()=>{
    assert.throws(()=>createPrimaryCaller({sendPresented:async()=>{}},'guarded-local',{},[],
      {maxExplicitObservations:value}),TypeError);
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
      feedback:{status:cue,expected_title:'saved',rejected_titles:[],title:'saved',after_title:'saved',task_success:null,authority_granted:false,input_dispatched:false},result:{status:'completed',execution:{releases:[
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


test('original presentation resends only retained bytes even after primary STOP', async () => {
  const directory=join(await mkdtemp(join(tmpdir(),'primary-original-')), 'host');
  const fixture=`require('node:readline').createInterface({input:process.stdin}).on('line',line=>{
    const r=JSON.parse(line); console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,
      result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'returned',call_id:'c1',
      source:{sequence:1,observation_id:'o1'}})},{type:'image',data:'AAECAw==',mimeType:'image/png'}]}}));});`;
  const host=await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],
    evidenceDirectory:directory,reuseReviewedImages:true});
  const seen=[]; const caller=createPrimaryCaller(host,'guarded-local',{
    text:value=>seen.push(value), image:value=>seen.push(value.bytes.toString('base64'))});
  try {
    const original=await caller.observe();
    await caller.review(original.attempt,{task:'t',phase:'initial',reason:'Original attribution, not semantic proof'});
    const reply=await readFile(join(directory,'reply-1.json'));
    const review=await readFile(join(directory,'review-1.json'));
    await assert.rejects(caller.observe('not allowed'));
    const stopped=caller.state().stopped;
    const first=seen.slice();
    await caller.presentOriginal(original.attempt);
    assert.deepEqual(seen.slice(first.length),first,'force the original image instead of an image reference');
    assert.equal(host.state().attempts,1,'no second relay request or capture');
    assert.equal(caller.state().stopped,stopped);
    assert.deepEqual(await readFile(join(directory,'reply-1.json')),reply);
    assert.deepEqual(await readFile(join(directory,'review-1.json')),review);
    const rows=(await readFile(join(directory,'host-events.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
    assert.equal(rows.filter(row=>row.kind==='send_requested').length,1);
    const shown=rows.filter(row=>row.kind==='presentation_callbacks_completed');
    assert.equal(shown.length,2);
    assert.equal(shown[0].reply_sha256,shown[1].reply_sha256);
    assert.equal(shown[1].image_delivery.mode,'full');
    await assert.rejects(caller.observe(),/stopped/);
    assert.equal(host.state().attempts,1);
  } finally { await host.close(); }
});

test('original presentation snapshots sinks and preserves the host exception', async () => {
  const firstText=()=>{}, firstImage=()=>{};
  const sinks={text:firstText,image:firstImage}; let submitted;
  const error=new Error('presentation failed');
  const caller=createPrimaryCaller({present:async(attempt,callbacks,options)=>{
    submitted={attempt,callbacks,options}; await Promise.resolve(); throw error;
  }},'guarded-local',sinks);
  const pending=caller.presentOriginal(3);
  sinks.text=()=>assert.fail('changed text'); sinks.image=()=>assert.fail('changed image');
  await assert.rejects(pending,value=>value===error);
  assert.deepEqual(submitted,{attempt:3,callbacks:{text:firstText,image:firstImage},options:{forceImage:true}});
  assert.ok(caller.state().stopped);
});

for (const args of [[],[0],[1.5],['1'],[1,{forceImage:false}]])
  test('original presentation rejects invalid arguments before host: '+JSON.stringify(args),async()=>{
    let calls=0;const caller=createPrimaryCaller({present:()=>{calls++;}},'guarded-local',{
      text:()=>{},image:()=>{}});
    await assert.rejects(caller.presentOriginal(...args),TypeError);
    assert.equal(calls,0);assert.ok(caller.state().stopped);
  });

test('missing original presentation sinks refuse before the host',async()=>{
  let calls=0; const caller=createPrimaryCaller({present:()=>{calls++;}},'guarded-local',{});
  await assert.rejects(caller.presentOriginal(1),TypeError);
  assert.equal(calls,0);assert.ok(caller.state().stopped);
});


for (const corruption of ['unknown-attempt','changed-reply'])
  test('original presentation fails closed on '+corruption+' without another relay request',async()=>{
    const directory=join(await mkdtemp(join(tmpdir(),'primary-original-invalid-')),'host');
    const fixture=`require('node:readline').createInterface({input:process.stdin}).on('line',line=>{
      const r=JSON.parse(line);console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,
      result:{content:[{type:'text',text:JSON.stringify({status:'returned',source:{sequence:1}})},
      {type:'image',mimeType:'image/png',data:'AAECAw=='}]}}));});`;
    const host=await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory:directory});
    let delivered=0; const caller=createPrimaryCaller(host,'guarded-local',{
      text:()=>{delivered++;},image:()=>{delivered++;}});
    try {
      const original=await caller.observe();const before=delivered;
      if(corruption==='changed-reply') {
        const path=join(directory,'reply-1.json');
        await writeFile(path,Buffer.concat([await readFile(path),Buffer.from(' ')]));
      }
      await assert.rejects(caller.presentOriginal(corruption==='unknown-attempt'?2:original.attempt),
        /delivered attempt|retained bytes differ/);
      assert.equal(delivered,before,'unverified source must not be delivered');
      assert.ok(caller.state().stopped);assert.ok(host.state().host_blocked);
      await assert.rejects(caller.call('interface_guarded_input',{}),/stopped/);
      assert.equal(host.state().attempts,1);
    } finally {await host.close();}
  });


test('original presentation sink getter failure stops before dispatch and preserves its exception',async()=>{
  const error=new TypeError('sink getter failed');let calls=0;
  const sinks={get text(){throw error;},image:()=>{}};
  const caller=createPrimaryCaller({present:()=>{calls++;},sendPresented:()=>{calls++;}},'guarded-local',sinks);
  await assert.rejects(caller.presentOriginal(1),value=>value===error);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.call('interface_clock',{}),/stopped/);
  assert.equal(calls,0);
});

// The public modal tools already exist. Removing either from the direct route
// must break this test; no synthetic task success or automatic selection is used.
for (const [tool, args, metadata] of [
  ['interface_inspect_target', {target:'app',screen_region:[0,0,640,480]},
    {status:'needs_review',input_dispatched:false,authority_granted:false,
      review_request:{tool:'interface_review_target',arguments:{target:'app',window_id:21,review_id:'once'}}}],
  ['interface_review_target', {target:'app',window_id:21,review_id:'once',screen_region:[0,0,640,480]},
    {status:'target_reviewed',input_dispatched:false,authority_granted:false,binding_revision:2}],
]) test('direct primary forwards one explicit '+tool+' without following its result',async()=>{
  const calls=[];
  const reply={attempt:1,result:{isError:false,content:[{type:'text',text:JSON.stringify(metadata)}]}};
  const caller=createPrimaryCaller({sendPresented:async(t,a)=>{calls.push([t,a]);return reply;}},'direct-post',{});
  assert.equal(await caller.call(tool,args),reply);
  assert.deepEqual(calls,[[tool,args]],'inspection must not auto-select, and selection must not auto-input');
  assert.equal(caller.state().stopped,null);
});

test('direct primary returns failed target selection once and blocks inspection/review retry',async()=>{
  let calls=0;
  const reply={result:{isError:true,content:[{type:'text',text:JSON.stringify({status:'needs_review',error:'target changed',input_dispatched:false,authority_granted:false})}]}};
  const caller=createPrimaryCaller({sendPresented:async()=>{calls++;return reply;}},'direct-post',{});
  assert.equal(await caller.call('interface_review_target',{target:'app',window_id:21,review_id:'once'}),reply);
  assert.ok(caller.state().stopped);
  await assert.rejects(caller.call('interface_inspect_target',{target:'app'}),/trial stopped/);
  await assert.rejects(caller.call('interface_review_target',{target:'app',window_id:21,review_id:'once'}),/trial stopped/);
  assert.equal(calls,1);
});

test('guarded primary rejects persistent target tools locally',async()=>{
  let calls=0;
  const caller=createPrimaryCaller({sendPresented:async()=>{calls++;}},'guarded-local',{});
  await assert.rejects(caller.call('interface_inspect_target',{target:'app'}),/unavailable tool/);
  assert.equal(calls,0);
  await assert.rejects(caller.call('interface_guarded_observe',{}),/trial stopped/);
});
