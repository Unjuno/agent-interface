import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRelayClient, presentRelayResponse } from './native_relay_client_v1.mjs';

const fixture = `
const readline=require('node:readline');let next=1;
readline.createInterface({input:process.stdin}).on('line',line=>{
 const r=JSON.parse(line);
 if(r.tool==='die'){process.exit(17);return;}
 if(r.tool==='refuse'){console.log(JSON.stringify({status:'refused',dispatched:false,next_id:next}));return;}
 const response={id:r.id,tool:r.tool,status:'returned',next_id:++next,result:{content:[{type:'text',text:JSON.stringify(r.arguments)},{type:'image',data:'AAECAw==',mimeType:'image/png'}]}};
 if(r.tool==='mismatch')response.id+=1;
 setTimeout(()=>console.log(JSON.stringify(response)),80);
});`;
async function setup() {
 const root=await mkdtemp(join(tmpdir(),'native-relay-client-'));
 const evidenceDirectory=join(root,'evidence');
 return {evidenceDirectory,client:await createRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory})};
}
test('one pending call survives interrupted waiting; no resend, exact content presentation',async()=>{
 const {client,evidenceDirectory}=await setup();
 const args={literal:'é',nested:{observation_ref:'/literal'}};
 const pending=client.send('native_submit',args);args.literal='changed';
 assert.throws(()=>client.send('native_submit',{}),/outstanding/);
 assert.equal(client.wait(),pending);
 const timeout=await Promise.race([pending.then(()=>false),new Promise(r=>setTimeout(()=>r(true),5))]);
 assert.equal(timeout,true);
 const result=await client.wait();
 assert.equal(client.wait(),pending);
 const text=[],images=[];
 await presentRelayResponse(result,{text:v=>text.push(v),image:v=>images.push(v)});
 assert.equal(JSON.parse(text[0]).literal,'é');
 assert.deepEqual([...images[0].bytes],[0,1,2,3]);
 assert.equal((await readdir(evidenceDirectory)).filter(n=>n.startsWith('request-')).length,1);
 assert.equal(JSON.parse(await readFile(join(evidenceDirectory,'request-1.json'))).arguments.literal,'é');
 assert.equal((await client.close()).code,0);
});
test('refused IDs can remain unchanged while attempt records never overwrite',async()=>{
 const {client,evidenceDirectory}=await setup();
 assert.equal((await client.send('refuse')).next_id,1);
 assert.equal((await client.send('native_status')).id,1);
 assert.deepEqual(client.state().attempts,2);
 assert.equal(JSON.parse(await readFile(join(evidenceDirectory,'request-2.json'))).id,1);
 await client.close();
});
test('process loss makes delivery uncertain and blocks new sends',async()=>{
 const {client}=await setup();
 await assert.rejects(client.send('die'),/delivery is uncertain/);
 assert.throws(()=>client.send('native_submit'),/relay exited/);
 assert.equal((await client.close()).code,17);
});
test('mismatched response retained but never presented as the pending result',async()=>{
 const {client,evidenceDirectory}=await setup();
 await assert.rejects(client.send('mismatch'),/identity/);
 assert.equal(JSON.parse(await readFile(join(evidenceDirectory,'reply-1.json'))).id,2);
 assert.throws(()=>client.send('native_status'),/identity/);
 await client.close();
});
test('existing evidence directory is refused before spawn',async()=>{
 const root=await mkdtemp(join(tmpdir(),'native-relay-existing-'));
 await assert.rejects(createRelayClient({command:'must-not-launch',args:[],evidenceDirectory:root}),/EEXIST/);
});
test('nonfinite or omitted values are refused before recording or sending',async()=>{
 const {client,evidenceDirectory}=await setup();
 for(const value of [NaN,Infinity,undefined,()=>{},Symbol('x')]) {
   assert.throws(()=>client.send('native_submit',{value}),/finite JSON/);
 }
 assert.equal(client.state().attempts,0);
 assert.equal((await readdir(evidenceDirectory)).filter(n=>n.startsWith('request-')).length,0);
 await client.close();
});
test('review attribution comes from explicit retained reply and cannot overwrite history', async () => {
 const { writeFile } = await import('node:fs/promises');
 const { createHash } = await import('node:crypto');
 const { recordRelayReview } = await import('./native_relay_client_v1.mjs');
 const root = await mkdtemp(join(tmpdir(), 'relay-review-'));
 const replyPath = join(root, 'reply-21.json'), receiptPath = join(root, 'review.json');
 const report = {call_id:'call-21',source:{sequence:59,observation_id:'observation-59'}};
 const row = {id:21,tool:'interface_guarded_input',status:'returned',result:{content:[
  {type:'text',text:JSON.stringify(report)}, {type:'image',data:'AAECAw==',mimeType:'image/png'}]}};
 const raw = JSON.stringify(row);
 await writeFile(replyPath,raw);
 const args = {replyPath,receiptPath,task:'task-4',phase:'entered',reason:'Caller declares image reviewed.'};
 const receipt = await recordRelayReview(args);
 assert.equal(receipt.call_id,'call-21'); assert.equal(receipt.source_sequence,59);
 assert.equal(receipt.observation_id,'observation-59'); assert.equal(receipt.relay_id,21);
 assert.equal(receipt.reply_sha256,createHash('sha256').update(raw).digest('hex'));
 assert.equal(receipt.images[0].sha256,createHash('sha256').update(Buffer.from([0,1,2,3])).digest('hex'));
 await assert.rejects(recordRelayReview(args),/EEXIST/);
 assert.deepEqual(JSON.parse(await readFile(receiptPath)),receipt);
});
test('public and management captures have explicit identity without invented sequence', async () => {
 const { writeFile } = await import('node:fs/promises');
 const { createHash } = await import('node:crypto');
 const { recordRelayReview } = await import('./native_relay_client_v1.mjs');
 const root=await mkdtemp(join(tmpdir(),'public-review-'));
 const hash=createHash('sha256').update(Buffer.from([0,1,2,3])).digest('hex');
 const capture={target:'app',native_window_id:123,frame:'screen_physical_px',region:[0,0,1,1],capture_started_ns:100,capture_ended_ns:200};
 const reports=[{call_id:'c',image_status:'image',image_reference:{sha256:hash,recorded_capture:capture}},
  {call_id:'m',image_status:'image',observation_report:{status:'returned',observation_id:'obs',observation:{...capture,artifact:{sha256:hash}}}}];
 for (let i=0;i<reports.length;i++) {
  const replyPath=join(root,`reply-${i}.json`),receiptPath=join(root,`review-${i}.json`);
  const row={id:i+1,tool:'interface_observe',status:'returned',result:{content:[{type:'text',text:JSON.stringify(reports[i])},{type:'image',mimeType:'image/png',data:'AAECAw=='}]}};
  await writeFile(replyPath,JSON.stringify(row));
  const receipt=await recordRelayReview({replyPath,receiptPath,task:'t',phase:'reviewed',reason:'explicit caller review'});
  assert.equal(receipt.source_sequence,null);assert.equal(receipt.capture.artifact_sha256,hash);
  assert.equal(receipt.schema,'agent-interface/primary-review-receipt-v2-public-capture');
  assert.equal(receipt.observation_id,i===0?null:'obs');
  row.result.content[1].data='AA==';await writeFile(replyPath,JSON.stringify(row));
  await assert.rejects(recordRelayReview({replyPath,receiptPath:receiptPath+'.bad',task:'t',phase:'reviewed',reason:'r'}),/matching delivered image/);
  await assert.rejects(readFile(receiptPath+'.bad'),/ENOENT/);
 }
});
test('review refuses ambiguous, missing-image, uncertain and incomplete evidence', async () => {
 const { writeFile } = await import('node:fs/promises');
 const { recordRelayReview } = await import('./native_relay_client_v1.mjs');
 const root = await mkdtemp(join(tmpdir(), 'relay-review-invalid-'));
 const text = {type:'text',text:JSON.stringify({call_id:'c',source:{sequence:1,observation_id:'o'}})};
 const image = {type:'image',data:'AA==',mimeType:'image/png'};
 const cases = [
  {id:1,status:'returned',result:{content:[text]}},
  {id:1,status:'returned',result:{content:[text,text,image]}},
  {id:1,status:'unknown_requires_reconciliation',result:{content:[text,image]}},
  {id:1,status:'returned',result:{content:[{type:'text',text:'{"call_id":"c","source":{"sequence":1}}'},image]}},
 ];
 for (let i=0;i<cases.length;i++) {
  const replyPath=join(root,`reply-${i}.json`),receiptPath=join(root,`receipt-${i}.json`);
  await writeFile(replyPath,JSON.stringify(cases[i]));
  await assert.rejects(recordRelayReview({replyPath,receiptPath,task:'t',phase:'p',reason:'r'}));
  await assert.rejects(readFile(receiptPath),/ENOENT/);
 }
});
