import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { createInstrumentedRelayClient } from './relay_host.mjs';

const fixture = `require('node:readline').createInterface({input:process.stdin}).on('line',line=>{
 const r=JSON.parse(line);
 const content=[{type:'text',text:JSON.stringify({call_id:'c'+r.id,status:'refused',error:'KeyError(4)',input_dispatched:false})}];
 if(r.tool==='image')content.push({type:'image',data:'AAECAw==',mimeType:'image/png'});
 console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{isError:true,content}}));
});`;
async function setup() {
 const dir=join(await mkdtemp(join(tmpdir(),'relay-text-ack-')),'transport');
 const client=await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory:dir});
 return {dir,client};
}
const attribution={task:'task4',phase:'revoked-source',reason:'Caller read the original text-only refusal.'};
const callbacks={text:()=>{},image:()=>{throw new Error('Unexpected image');}};

test('text acknowledgment retains original error and digest, without an image review or another request',async()=>{
 const {dir,client}=await setup();
 try {
  assert.equal(typeof client.acknowledgeText,'function','Host must support a separate text-only acknowledgment');
  const seen=[];
  const row=await client.sendPresented('revoked-source',{}, {...callbacks,text:value=>seen.push(value)});
  const original=await readFile(join(dir,'reply-1.json'));
  const receipt=await client.acknowledgeText(row.attempt,attribution);
  assert.equal(receipt.schema,'agent-interface/text-acknowledgment-v1');
  assert.equal(receipt.reply_sha256,createHash('sha256').update(original).digest('hex'));
  assert.equal(receipt.isError,true);
  assert.equal(receipt.relay_id,row.id);
  assert.equal(receipt.tool,'revoked-source');
  assert.equal(receipt.text_blocks,1);
  assert.ok(seen.some(value=>typeof value==='string'&&value.includes('KeyError(4)')));
  assert.deepEqual(await readFile(join(dir,'reply-1.json')),original);
  const names=await readdir(dir);
  assert.ok(names.includes('text-acknowledgment-1.json'));
  assert.ok(!names.includes('review-1.json'));
  assert.equal(names.filter(n=>n.startsWith('request-')).length,1);
  const events=(await readFile(join(dir,'host-events.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
  assert.equal(events.at(-1).kind,'text_acknowledgment_recorded');
  assert.equal(events.at(-2).kind,'presentation_callbacks_completed');
  assert.equal(events.at(-1).reply_sha256,receipt.reply_sha256);
  await assert.rejects(client.acknowledgeText(1,attribution),/EEXIST/);
  assert.deepEqual(JSON.parse(await readFile(join(dir,'text-acknowledgment-1.json'))),receipt);
  assert.throws(()=>client.send('replay'),/host evidence incomplete/);
 } finally {await client.close();}
});

for(const condition of ['unpresented','changed-reply','image']) {
 test(`text acknowledgment rejects ${condition} without a receipt`,async()=>{
  const {dir,client}=await setup();
  try {
   assert.equal(typeof client.acknowledgeText,'function');
   await client.send(condition==='image'?'image':'revoked-source');
   if(condition!=='unpresented')await client.present(1,{text:()=>{},image:()=>{}});
   if(condition==='changed-reply') {
    const path=join(dir,'reply-1.json');const row=JSON.parse(await readFile(path));
    row.result.isError=false;await writeFile(path,JSON.stringify(row));
   }
   await assert.rejects(client.acknowledgeText(1,attribution),condition==='image'?/text-only/:condition==='changed-reply'?/delivered reply/:/completed presentation/);
   assert.ok(!(await readdir(dir)).includes('text-acknowledgment-1.json'));
   assert.equal(client.state().attempts,1);
  } finally {await client.close();}
 });
}

test('text acknowledgment cannot replace strict image review',async()=>{
 const {dir,client}=await setup();
 try {
  await client.sendPresented('revoked-source',{},callbacks);
  await assert.rejects(client.review(1,attribution),/one sourced report and delivered image required/);
  assert.ok(!(await readdir(dir)).includes('review-1.json'));
 } finally {await client.close();}
});

test('changed retained reply cannot be presented as the original delivered response',async()=>{
 const {dir,client}=await setup();
 try {
  await client.send('revoked-source');
  const path=join(dir,'reply-1.json');const row=JSON.parse(await readFile(path));
  row.result.content[0].text='replacement';await writeFile(path,JSON.stringify(row));
  const seen=[];
  await assert.rejects(client.present(1,{text:value=>seen.push(value),image:()=>{}}),/delivered reply/);
  assert.deepEqual(seen,[]);
  assert.ok(!(await readdir(dir)).includes('text-acknowledgment-1.json'));
 } finally {await client.close();}
});
