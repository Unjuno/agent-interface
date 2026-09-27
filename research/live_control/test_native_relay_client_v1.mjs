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