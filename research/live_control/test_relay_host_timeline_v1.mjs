import test from 'node:test';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
import { mkdtemp,readFile,rename,mkdir,readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInstrumentedRelayClient } from './relay_host_timeline_v1.mjs';
const fixture=`const rl=require('node:readline');rl.createInterface({input:process.stdin}).on('line',line=>{
 const r=JSON.parse(line);const report={call_id:'c'+r.id,source:{sequence:r.id,observation_id:'o'+r.id},args:r.arguments};
 setTimeout(()=>console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{content:[{type:'text',text:JSON.stringify(report)},{type:'image',data:'AAECAw==',mimeType:'image/png'}]}})),40);
});`;
async function setup(options={}){const root=await mkdtemp(join(tmpdir(),'relay-host-timeline-'));const dir=join(root,'transport');return {dir,client:await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory:dir,...options})};}
async function events(dir){return (await readFile(join(dir,'host-events.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);}
test('ordered same-clock events separate transport, presentation and caller review before next send',async()=>{
 const {dir,client}=await setup();const args={value:'original'};const p=client.send('observe',args);args.value='mutated';
 assert.equal(client.wait(),p);assert.throws(()=>client.send('duplicate'),/outstanding/);
 const row=await p;assert.equal(JSON.parse(row.result.content[0].text).args.value,'original');
 let release;const gate=new Promise(r=>{release=r});let entered;const ready=new Promise(r=>{entered=r});
 const presentation=client.present(1,{text:()=>{},image:async()=>{entered();await gate;}});
 await ready;assert.throws(()=>client.send('early'),/outstanding/);await assert.rejects(client.close(),/outstanding/);
 assert.equal((await events(dir)).at(-1).kind,'presentation_started');release();await presentation;
 await client.review(1,{task:'t',phase:'entered',reason:'Caller reviewed image.'});
 await client.send('save');await client.close();
 const rows=await events(dir);
 assert.deepEqual(rows.map(r=>r.kind),['send_requested','reply_available','presentation_started','presentation_callbacks_completed','review_recorded','send_requested','reply_available','transport_closed']);
 assert.deepEqual(rows.map(r=>r.sequence),[1,2,3,4,5,6,7,8]);
 for(let i=1;i<rows.length;i++)assert.ok(rows[i].host_monotonic_ms>=rows[i-1].host_monotonic_ms);
 assert.equal(rows[4].call_id,'c1');assert.equal(rows[4].reply_sha256,rows[1].reply_sha256);
 assert.equal(JSON.parse(await readFile(join(dir,'review-1.json'))).source_sequence,1);
});
test('public capture review joins the same host timeline without a fabricated source sequence',async()=>{
 const {createHash}=await import('node:crypto');
 const digest=createHash('sha256').update(Buffer.from([0,1,2,3])).digest('hex');
 const source=`image_status:'image',image_reference:{sha256:'${digest}',recorded_capture:{target:'app',native_window_id:10,frame:'window_client',region:[0,0,1,1],capture_started_ns:100,capture_ended_ns:101}}`;
 const publicFixture=fixture.replace('source:{sequence:r.id,observation_id:\'o\'+r.id}',source);
 const root=await mkdtemp(join(tmpdir(),'public-host-review-'));const dir=join(root,'transport');
 const client=await createInstrumentedRelayClient({command:process.execPath,args:['-e',publicFixture],evidenceDirectory:dir});
 await client.send('interface_observe');await client.present(1,{text:()=>{},image:()=>{}});
 const receipt=await client.review(1,{task:'t',phase:'visible',reason:'Caller reviewed public image.'});
 assert.equal(receipt.source_sequence,null);assert.equal(receipt.capture.artifact_sha256,digest);
 const rows=await events(dir);assert.equal(rows.at(-1).kind,'review_recorded');
 assert.equal(rows.at(-1).source_sequence,null);assert.equal(rows.at(-1).reply_sha256,receipt.reply_sha256);
 assert.equal(rows.at(-2).kind,'presentation_callbacks_completed');await client.close();
});
test('failed instrumentation before send emits no request and transport remains closable',async()=>{
 const {dir,client}=await setup();const path=join(dir,'host-events.jsonl');await rename(path,path+'.original');await mkdir(path);
 await assert.rejects(client.send('must-not-send'));
 assert.equal(client.state().attempts,0);assert.throws(()=>client.send('retry'));
 assert.equal((await readdir(dir)).filter(n=>n.startsWith('request-')).length,0);
 await assert.rejects(client.close());
 assert.equal(JSON.parse(await readFile(join(dir,'exit.json'))).code,0);
});
test('presentation failure is retained as a started-only boundary and blocks later action',async()=>{
 const {dir,client}=await setup();await client.send('observe');
 await assert.rejects(client.present(1,{text:()=>{},image:()=>{throw new Error('renderer failed')}}),/renderer failed/);
 assert.throws(()=>client.send('save'),/renderer failed/);
 await client.close();assert.deepEqual((await events(dir)).map(r=>r.kind),['send_requested','reply_available','presentation_started','transport_closed']);
});
test('invalid JSON does not consume an attempt and foreign review cannot gain an event',async()=>{
 const {dir,client}=await setup();assert.throws(()=>client.send('observe',{value:NaN}),/finite JSON/);
 assert.equal(client.state().attempts,0);await client.send('observe');
 await assert.rejects(client.review(2,{task:'t',phase:'entered',reason:'r'}),/delivered attempt/);
 assert.throws(()=>client.send('save'));await client.close();
 assert.equal((await events(dir)).filter(r=>r.kind==='review_recorded').length,0);
});
test('timeline loss after submission retains reply and blocks replay while allowing transport cleanup',async()=>{
 const root=await mkdtemp(join(tmpdir(),'relay-host-after-send-'));const dir=join(root,'transport');
 const client=await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture.replace(')),40);',')),250);')],evidenceDirectory:dir});
 const pending=client.send('input');
 let requestSeen=false;
 for(let i=0;i<100;i++) {
  try {await readFile(join(dir,'request-1.json'));requestSeen=true;break;}
  catch(error){if(error.code!=='ENOENT')throw error;}
  await new Promise(resolve=>setTimeout(resolve,2));
 }
 assert.equal(requestSeen,true);
 const path=join(dir,'host-events.jsonl');await rename(path,path+'.original');await mkdir(path);
 await assert.rejects(pending,/never infer no input or replay/);assert.equal(client.wait(),pending);
 assert.equal(JSON.parse(await readFile(join(dir,'reply-1.json'))).status,'returned');
 assert.equal(client.state().attempts,1);assert.throws(()=>client.send('retry'));
 await assert.rejects(client.close());
 assert.equal(JSON.parse(await readFile(join(dir,'exit.json'))).code,0);
});

test('opt-in image reuse requires explicit presented review and retains original base',async()=>{
 const {dir,client}=await setup({reuseReviewedImages:true});const seen=[];
 const callbacks={text:v=>seen.push(['text',v]),image:v=>seen.push(['image',v.bytes.toString('hex')])};
 const show=async(n,options)=>{await client.send('observe',{n});await client.present(n,callbacks,options);};
 await show(1);await show(2);
 assert.equal(seen.filter(x=>x[0]==='image').length,2);
 await client.review(2,{task:'t',phase:'reviewed',reason:'Explicitly reviewed second full image.'});
 await show(3);
 assert.equal(seen.filter(x=>x[0]==='image').length,2);
 const reference=seen.filter(x=>x[1]?.schema==='agent-interface/reviewed-image-reference-v1').at(-1)[1];
 assert.equal(reference.base_attempt,2);assert.equal(reference.attempt,3);
 assert.ok(seen.some(x=>x[0]==='text'&&typeof x[1]==='string'&&JSON.parse(x[1]).args.n===3));
 await client.review(3,{task:'t',phase:'same-image',reason:'Reviewed unchanged image reference and current text.'});
 await show(4);assert.equal(seen.filter(x=>x[1]?.base_attempt===2).length,2);
 await show(5,{forceImage:true});await show(6);
 assert.equal(seen.filter(x=>x[0]==='image').length,4);
 await client.review(6,{task:'t',phase:'resynchronized',reason:'Explicit full-image review after reset.'});
 await show(7);await client.close();
 const rows=await events(dir);const starts=rows.filter(x=>x.kind==='presentation_started');
 assert.deepEqual(starts.map(x=>x.image_delivery.mode),['full','full','reviewed-image-reference','reviewed-image-reference','full','full','reviewed-image-reference']);
 assert.equal(starts.at(-1).image_delivery.base_attempt,6);
 assert.equal(rows.find(x=>x.kind==='review_recorded'&&x.attempt===3).image_delivery.base_attempt,2);
 // The transport reply always retains the full image; only presentation changes.
 assert.equal(JSON.parse(await readFile(join(dir,'reply-3.json'))).result.content[1].type,'image');
 // Validate the actual emitted cross-language evidence, including a reviewed reference.
 const audited=JSON.parse(execFileSync(process.env.PYTHON ?? 'python3',
   ['-m','runtime.integration_checks.host_timing',dir],{encoding:'utf8'}));
 assert.equal(audited.timeline_status,'complete');
 assert.equal(audited.calls[2].presentations[0].image_delivery.base_attempt,2);
 assert.equal(audited.calls[6].presentations[0].image_delivery.base_attempt,6);
 const fresh=await setup({reuseReviewedImages:true});let first=0;
 await fresh.client.send('observe');await fresh.client.present(1,{text:()=>{},image:()=>{first++;}});
 assert.equal(first,1);await fresh.client.close();
});
test('unpresented review cannot acknowledge an image base',async()=>{
 const {client}=await setup({reuseReviewedImages:true});
 await client.send('observe');await client.review(1,{task:'t',phase:'unpresented',reason:'Attribution only.'});
 await client.send('observe');let images=0;
 await client.present(2,{text:()=>{},image:()=>{images++;}});assert.equal(images,1);await client.close();
});
test('reference presentation failure blocks actions and cannot be treated as delivered',async()=>{
 const {client,dir}=await setup({reuseReviewedImages:true});
 await client.send('observe');await client.present(1,{text:()=>{},image:()=>{}});
 await client.review(1,{task:'t',phase:'visible',reason:'Explicit review.'});await client.send('observe');
 await assert.rejects(client.present(2,{text:v=>{if(typeof v==='object')throw Error('reference renderer failed');},image:()=>assert.fail('duplicate image emitted')}),/reference renderer failed/);
 assert.throws(()=>client.send('input'),/reference renderer failed/);await client.close();
 assert.equal((await events(dir)).filter(x=>x.kind==='presentation_callbacks_completed').length,1);
});
test('a changed PNG is forwarded and invalidates the previous acknowledged base',async()=>{
 const changed=fixture.replace("data:'AAECAw=='", "data:r.arguments.changed?'AAECAA==':'AAECAw=='");
 const {client}=await setup({reuseReviewedImages:true,args:['-e',changed]});let images=0;
 const callbacks={text:()=>{},image:()=>{images++;}};
 await client.send('observe');await client.present(1,callbacks);
 await client.review(1,{task:'t',phase:'visible',reason:'Explicit review.'});
 await client.send('observe',{changed:true});await client.present(2,callbacks);
 await client.send('observe');await client.present(3,callbacks);
 assert.equal(images,3);await client.close();
});
