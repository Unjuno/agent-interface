import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir, statfs } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRelayClient } from './relay_client.mjs';
import { createInstrumentedRelayClient } from './relay_host.mjs';

const fixture = `require('node:readline').createInterface({input:process.stdin}).on('line',line=>{const r=JSON.parse(line);console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{content:[{type:'text',text:'{}'}]}}));});`;

for (const [name, create] of [['relay',createRelayClient],['instrumented',createInstrumentedRelayClient]]) {
  test(`${name} refuses insufficient evidence headroom before child startup`, async()=>{
    const root=await mkdtemp(join(tmpdir(),'evidence-capacity-'));
    const evidenceDirectory=join(root,'evidence');
    let client, error;
    try {
      client=await create({command:process.execPath,args:['-e',fixture],evidenceDirectory,
        minimumEvidenceFreeBytes:Number.MAX_SAFE_INTEGER});
      // On the old implementation this exchange proves a child was started.
      await client.send('static-fixture-only');
    } catch (e) { error=e; }
    finally { if(client) await client.close(); }
    assert.ok(error,'insufficient capacity must reject construction before a child is returned');
    assert.equal(error.code,'EVIDENCE_CAPACITY');
    assert.match(error.message,/before relay startup/);
    assert.deepEqual(await readdir(root),[],'no allocation or child evidence when capacity rejects');
  });
}

test('successful preflight is retained separately from transport calls',async()=>{
  const root=await mkdtemp(join(tmpdir(),'evidence-capacity-receipt-'));
  const evidenceDirectory=join(root,'evidence');
  const client=await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],
    evidenceDirectory,minimumEvidenceFreeBytes:1024});
  try {
    const receipt=JSON.parse(await readFile(join(evidenceDirectory,'storage-preflight.json'),'utf8'));
    assert.equal(receipt.schema,'agent-interface/evidence-storage-preflight-v1');
    assert.equal(receipt.minimum_free_bytes,1024);
    assert.ok(BigInt(receipt.available_bytes)>=1024n);
    assert.equal(receipt.child_started,false);
    assert.equal(receipt.capacity_reserved,false);
    assert.equal(receipt.future_writes_guaranteed,false);
    assert.equal(client.state().attempts,0);
    assert.equal(await readFile(join(evidenceDirectory,'host-events.jsonl'),'utf8'),'');
    await client.send('static-fixture-only');
  } finally { await client.close(); }
});

test('invalid capacity floors reject before directory creation or child startup',async()=>{
  const root=await mkdtemp(join(tmpdir(),'evidence-capacity-invalid-'));
  for(const minimumEvidenceFreeBytes of [0,-1,1.5,NaN,Infinity,'1024',null]) {
    await assert.rejects(createRelayClient({command:process.execPath,args:['-e',fixture],
      evidenceDirectory:join(root,'evidence'),minimumEvidenceFreeBytes}).then(async client=>{
        // Clean up the old implementation's incorrectly accepted constructor too.
        await client.close(); return client;
      }),/positive safe integer/);
  }
  assert.deepEqual(await readdir(root),[]);
});

test('default capacity floor is recorded as a bounded startup check',async()=>{
  const root=await mkdtemp(join(tmpdir(),'evidence-capacity-default-'));
  const evidenceDirectory=join(root,'evidence');
  const client=await createRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory});
  try {
    const receipt=JSON.parse(await readFile(join(evidenceDirectory,'storage-preflight.json'),'utf8'));
    assert.equal(receipt.minimum_free_bytes,32*1024*1024);
    const fs=await statfs(evidenceDirectory,{bigint:true});
    assert.ok(fs.bsize>0n);
    assert.equal(receipt.observed_path,evidenceDirectory);
  } finally { await client.close(); }
});
