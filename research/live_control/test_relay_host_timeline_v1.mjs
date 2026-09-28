import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp,readFile,rename,mkdir,readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInstrumentedRelayClient } from './relay_host_timeline_v1.mjs';
const fixture=`const rl=require('node:readline');rl.createInterface({input:process.stdin}).on('line',line=>{
 const r=JSON.parse(line);const report={call_id:'c'+r.id,source:{sequence:r.id,observation_id:'o'+r.id},args:r.arguments};
 setTimeout(()=>console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{content:[{type:'text',text:JSON.stringify(report)},{type:'image',data:'AAECAw==',mimeType:'image/png'}]}})),40);
});`;
async function setup(){const root=await mkdtemp(join(tmpdir(),'relay-host-timeline-'));const dir=join(root,'transport');return {dir,client:await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory:dir})};}
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