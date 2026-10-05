import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRelayClient, presentRelayResponse } from './relay_client.mjs';

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
 const { recordRelayReview } = await import('./relay_client.mjs');
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
 const { recordRelayReview } = await import('./relay_client.mjs');
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
 const { recordRelayReview } = await import('./relay_client.mjs');
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

test('presentation preserves explicit MCP error status before unchanged content', async () => {
 for (const isError of [true, false]) {
  const row={status:'returned',result:{isError,content:[
   {type:'text',text:'same ambiguous body'},
   {type:'image',mimeType:'image/png',data:'AAECAw=='}
  ]}};
  const before=JSON.stringify(row),seen=[];
  await presentRelayResponse(row,{text:v=>seen.push(['text',v]),image:v=>seen.push(['image',v])});
  assert.deepEqual(seen[0],['text',{schema:'agent-interface/mcp-result-status-v1',isError}]);
  assert.deepEqual(seen[1],['text','same ambiguous body']);
  assert.deepEqual(seen[2],['image',{bytes:Buffer.from([0,1,2,3]),mimeType:'image/png'}]);
  assert.equal(JSON.stringify(row),before);
 }
});
test('presentation retains explicit error status for empty content and does not invent an absent flag', async () => {
 for (const result of [{isError:true,content:[]},{content:[]}]) {
  const seen=[];
  await presentRelayResponse({status:'returned',result},{text:v=>seen.push(v),image:()=>assert.fail('unexpected image')});
  assert.deepEqual(seen,Object.hasOwn(result,'isError')?[{schema:'agent-interface/mcp-result-status-v1',isError:true}]:[]);
 }
});


test('copied public host modules run outside the checkout using only Node built-ins', async () => {
  const { copyFile } = await import('node:fs/promises');
  const { pathToFileURL } = await import('node:url');
  const root = await mkdtemp(join(tmpdir(), 'public-relay-host-copy-'));
  for (const name of ['relay_client.mjs', 'relay_host.mjs']) {
    await copyFile(new URL(name, import.meta.url), join(root, name));
  }
  const module = await import(pathToFileURL(join(root, 'relay_host.mjs')).href);
  const client = await module.createInstrumentedRelayClient({
    command: process.execPath, args: ['-e', fixture], evidenceDirectory: join(root, 'evidence') });
  const response = await client.send('interface_validate', { program: {} });
  const texts = [], images = [];
  await client.present(response.attempt, { text: value => texts.push(value), image: value => images.push(value) });
  assert.equal(response.attempt, 1);
  assert.equal(JSON.parse(texts[0]).program.constructor, Object);
  assert.deepEqual([...images[0].bytes], [0, 1, 2, 3]);
  assert.equal((await client.close()).code, 0);
});

// An already failed reply journal must not suppress the new terminal receipt.
// All failures below use actual child pipes and exclusive files, not mocked I/O.
const exitJournalFixture = `
const readline=require('node:readline');let requests=0;
const guard=setTimeout(()=>process.exit(73),3000);
const lines=readline.createInterface({input:process.stdin});
lines.on('line',line=>{
 requests++;const r=JSON.parse(line);
 if(r.tool==='invalid-json'){console.log('{broken');return;}
 console.log(JSON.stringify({id:r.id+(r.tool==='wrong-id'?1:0),tool:r.tool,
   status:'returned',next_id:r.id+1,result:{content:[]}}));
});
lines.on('close',()=>{clearTimeout(guard);process.exitCode=requests===1?0:74;});`;

async function exitJournalCase({tool='wrong-id',occupiedReply=false,occupiedExit=false}) {
  const {writeFile}=await import('node:fs/promises');
  const root=await mkdtemp(join(tmpdir(),'relay-exit-journal-'));
  const evidenceDirectory=join(root,'evidence');
  const client=await createRelayClient({command:process.execPath,args:['-e',exitJournalFixture],evidenceDirectory});
  const sentinel='owned original evidence\n';
  let closed=false;
  try {
    if(occupiedReply)await writeFile(join(evidenceDirectory,'reply-1.json'),sentinel,{flag:'wx'});
    if(occupiedExit)await writeFile(join(evidenceDirectory,'exit.json'),sentinel,{flag:'wx'});
    const pending=client.send(tool,{});
    assert.equal(client.wait(),pending);
    if(tool==='valid'&&!occupiedReply)await pending;
    else {
      await assert.rejects(pending,/delivery is uncertain/);
      assert.equal(client.wait(),pending);
      assert.throws(()=>client.send('valid',{}));
    }
    const outcome=await client.close();closed=true;
    assert.equal(outcome.code,0);assert.equal(outcome.signal,null);
    assert.equal((await readdir(evidenceDirectory)).filter(n=>n.startsWith('request-')).length,1);
    return {evidenceDirectory,outcome,sentinel};
  } finally {if(!closed)await client.close();}
}

test('wrong response identity still retains actual exit and original journal error',async()=>{
  const {evidenceDirectory,outcome}=await exitJournalCase({});
  const exit=JSON.parse(await readFile(join(evidenceDirectory,'exit.json'),'utf8'));
  assert.deepEqual(exit,outcome);assert.match(exit.journal_error,/identity\/status mismatch/);
  assert.equal(JSON.parse(await readFile(join(evidenceDirectory,'reply-1.json'),'utf8')).id,2);
});
test('invalid reply JSON still retains actual exit without retrying the request',async()=>{
  const {evidenceDirectory,outcome}=await exitJournalCase({tool:'invalid-json'});
  assert.deepEqual(JSON.parse(await readFile(join(evidenceDirectory,'exit.json'),'utf8')),outcome);
  assert.match(outcome.journal_error,/SyntaxError/);
  assert.equal(await readFile(join(evidenceDirectory,'reply-1.json'),'utf8'),'{broken\n');
});
test('occupied original reply file still allows a new terminal receipt',async()=>{
  const {evidenceDirectory,outcome,sentinel}=await exitJournalCase({tool:'valid',occupiedReply:true});
  assert.deepEqual(JSON.parse(await readFile(join(evidenceDirectory,'exit.json'),'utf8')),outcome);
  assert.match(outcome.journal_error,/EEXIST/);
  assert.equal(await readFile(join(evidenceDirectory,'reply-1.json'),'utf8'),sentinel);
});
test('failed reply journal and occupied exit preserve both errors and original exit bytes',async()=>{
  const {evidenceDirectory,outcome,sentinel}=await exitJournalCase({occupiedExit:true});
  assert.match(outcome.journal_error,/identity\/status mismatch/);
  assert.match(outcome.exit_journal_error,/EEXIST/);
  assert.equal(await readFile(join(evidenceDirectory,'exit.json'),'utf8'),sentinel);
});
test('healthy reply journal preserves the existing occupied-exit error behavior',async()=>{
  const {evidenceDirectory,outcome,sentinel}=await exitJournalCase({tool:'valid',occupiedExit:true});
  assert.match(outcome.journal_error,/EEXIST/);
  assert.equal(Object.hasOwn(outcome,'exit_journal_error'),false);
  assert.equal(await readFile(join(evidenceDirectory,'exit.json'),'utf8'),sentinel);
});



const replyReaderProbe = "import cp from 'node:child_process';\nimport { syncBuiltinESMExports } from 'node:module';\nimport { readdir } from 'node:fs/promises';\nimport { once } from 'node:events';\n\nconst [moduleUrl, scenario, evidenceDirectory] = process.argv.slice(1);\nconst originalSpawn = cp.spawn;\nlet child;\ncp.spawn = (...args) => {\n  child = originalSpawn(...args);\n  return child;\n};\nsyncBuiltinESMExports();\nconst { createRelayClient } = await import(moduleUrl);\nconst fixture = `\nconst readline=require('node:readline');\nconst timer=setTimeout(()=>process.exit(31),2000);\nconst input=readline.createInterface({input:process.stdin});\ninput.on('close',()=>{clearTimeout(timer);process.exit(0);});\ninput.on('line',async line=>{\n  const r=JSON.parse(line);\n  process.stderr.write('COMMITTED '+r.id+'\\\\n');\n  if(r.tool==='pending')return;\n  const row={id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,\n    result:{content:[{type:'text',text:r.arguments.literal}]}};\n  const bytes=Buffer.from(JSON.stringify(row)+'\\\\n','utf8');\n  for(const byte of bytes){process.stdout.write(Buffer.from([byte]));\n    await new Promise(resolve=>setImmediate(resolve));}\n});`;\nconst client = await createRelayClient({ command: process.execPath,\n  args: ['-e', fixture], evidenceDirectory });\nconsole.log(JSON.stringify({ stage: 'created', child_pid: child.pid, scenario }));\nconst fault = () => child.stdout.destroy(new Error('injected relay reply read fault'));\nlet pending, outcome, samePromise = null, committed = false;\nconst literal = '\\u685c\\u306e\\u8a18\\u9332\\ud83d\\ude00';\nif (scenario === 'idle') {\n  const closed = once(child.stdout, 'close').catch(() => {});\n  fault();\n  await closed;\n} else {\n  let stderr = '';\n  const commitment = new Promise(resolve => child.stderr.on('data', chunk => {\n    stderr += chunk.toString('utf8');\n    if (stderr.includes('COMMITTED 1\\n')) resolve();\n  }));\n  pending = client.send(scenario === 'pending' ? 'pending' : 'unicode', { literal });\n  await commitment;\n  committed = true;\n  console.log(JSON.stringify({ stage: 'committed', scenario, state: client.state() }));\n  samePromise = client.wait() === pending;\n  if (scenario === 'pending') {\n    fault();\n    try { await pending; outcome = 'unexpected-return'; }\n    catch (error) { outcome = String(error); }\n  } else {\n    outcome = await pending;\n    if (scenario === 'settled') {\n      const closed = once(child.stdout, 'close').catch(() => {});\n      fault();\n      await closed;\n      samePromise = samePromise && client.wait() === pending && await client.wait() === outcome;\n    }\n  }\n}\nlet newSendBlocked = null;\nif (scenario !== 'unicode') {\n  try { client.send('unicode', { literal }); newSendBlocked = false; }\n  catch (error) { newSendBlocked = String(error).includes('injected relay reply read fault'); }\n}\nconst beforeClose = client.state();\nconst exit = await client.close();\nconst entries = await readdir(evidenceDirectory);\nconsole.log(JSON.stringify({ stage: 'result', scenario, committed, outcome,\n  samePromise, newSendBlocked, beforeClose, exit,\n  requestFiles: entries.filter(name => name.startsWith('request-')).sort(),\n  replyFiles: entries.filter(name => name.startsWith('reply-')).sort(),\n  literal, fixture: 'real inert Node child; injected real stdout stream destroy; responsive private files; child self-exit cap2000ms' }));\n";

async function runReplyReaderCase(scenario) {
  const { spawnSync } = await import('node:child_process');
  const root = await mkdtemp(join(tmpdir(), 'relay-reply-reader-'));
  const evidenceDirectory = join(root, 'evidence');
  const result = spawnSync(process.execPath,
    ['--input-type=module', '--eval', replyReaderProbe,
     new URL('./relay_client.mjs', import.meta.url).href, scenario, evidenceDirectory],
    { encoding: 'utf8', timeout: 5000, maxBuffer: 128 * 1024, windowsHide: true });
  assert.equal(result.status, 0, JSON.stringify({error: String(result.error),
    signal: result.signal, stdout: result.stdout, stderr: result.stderr}));
  const rows = result.stdout.trim().split('\n').map(line => JSON.parse(line));
  const outcome = rows.at(-1);
  assert.equal(outcome.stage, 'result');
  assert.equal(outcome.exit.code, 0);
  assert.equal(outcome.beforeClose.pending, false);
  return outcome;
}
test('reply reader failure before a request blocks delivery without consuming an ID', async () => {
  const row = await runReplyReaderCase('idle');
  assert.equal(row.newSendBlocked, true);
  assert.equal(row.beforeClose.nextId, 1);
  assert.equal(row.beforeClose.attempts, 0);
  assert.match(row.beforeClose.blocked, /injected relay reply read fault/);
  assert.deepEqual(row.requestFiles, []);
  assert.deepEqual(row.replyFiles, []);
});
test('reply reader failure rejects the same outstanding promise and forbids replay', async () => {
  const row = await runReplyReaderCase('pending');
  assert.equal(row.committed, true);
  assert.equal(row.samePromise, true);
  assert.match(row.outcome, /delivery is uncertain.*never replay/);
  assert.equal(row.newSendBlocked, true);
  assert.equal(row.beforeClose.nextId, 1);
  assert.equal(row.beforeClose.attempts, 1);
  assert.deepEqual(row.requestFiles, ['request-1.json']);
  assert.deepEqual(row.replyFiles, []);
});
test('reply reader failure preserves an already settled result and blocks future delivery', async () => {
  const row = await runReplyReaderCase('settled');
  assert.equal(row.samePromise, true);
  assert.equal(row.outcome.status, 'returned');
  assert.equal(row.outcome.result.content[0].text, row.literal);
  assert.equal(row.newSendBlocked, true);
  assert.equal(row.beforeClose.nextId, 2);
  assert.equal(row.beforeClose.attempts, 1);
  assert.deepEqual(row.requestFiles, ['request-1.json']);
  assert.deepEqual(row.replyFiles, ['reply-1.json']);
});
test('reply reader retains fragmented multilingual responses and normal EOF', async () => {
  const row = await runReplyReaderCase('unicode');
  assert.equal(row.samePromise, true);
  assert.equal(row.outcome.result.content[0].text, row.literal);
  assert.equal(row.beforeClose.blocked, null);
  assert.equal(row.beforeClose.nextId, 2);
  assert.deepEqual(row.requestFiles, ['request-1.json']);
  assert.deepEqual(row.replyFiles, ['reply-1.json']);
});
