import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, copyFile, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createInstrumentedRelayClient } from '../../../runtime/host_v1/relay_host.mjs';
import { createPrimaryCaller } from '../../../runtime/host_v1/primary_caller.mjs';

const source = fileURLToPath(new URL('../../live_control/results/recovery-assistant-01/', import.meta.url));
const selected = ['006.png', '007.png', '008.png', '009.png'];
const tools = ['interface_guarded_input', 'interface_guarded_observe',
  'interface_guarded_input', 'interface_guarded_observe'];
const fixture = String.raw`
const {readFileSync}=require('node:fs');
const {join}=require('node:path');
const readline=require('node:readline');
const expected=JSON.parse(process.argv[2]);
const root=process.argv[3];
let n=0;
readline.createInterface({input:process.stdin}).on('line',line=>{
  const req=JSON.parse(line), row=expected[n++];
  if(!row || req.tool!==row.tool){process.stderr.write('unexpected request '+req.tool+' at '+(n-1));process.exitCode=71;return;}
  const meta=row.tool==='interface_guarded_input'
    ? {status:'completed',image_status:'image',task_success:null,
       result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}}
    : {status:'returned',image_status:'image',task_success:null,source:{sequence:row.sequence}};
  meta.call_id='c'+n;
  meta.source={sequence:row.sequence,observation_id:'o'+row.sequence};
  process.stdout.write(JSON.stringify({id:req.id,tool:req.tool,status:'returned',next_id:req.id+1,
    result:{isError:false,content:[{type:'text',text:JSON.stringify(meta)},
      {type:'image',data:readFileSync(join(root,row.file)).toString('base64'),mimeType:'image/png'}]}})+'\n');
});
`;

test('retained unpainted/stale Calc frames traverse the current primary host as bounded explicit observations', async () => {
  const temp=await mkdtemp(join(tmpdir(),'handoff-replay-57-'));
  const evidence=join(temp,'evidence');
  const frames=join(temp,'frames');
  await mkdir(frames);
  for(const name of selected) await copyFile(join(source,name),join(frames,name));
  const sequence=selected.map((file,i)=>({tool:tools[i],file,sequence:i+6}));
  const script=join(temp,'fixture.cjs');
  await writeFile(script,fixture);
  const host=await createInstrumentedRelayClient({command:process.execPath,
    args:[script,JSON.stringify(sequence),frames],evidenceDirectory:evidence});
  const seenImages=[];
  const caller=createPrimaryCaller(host,'guarded-local',{
    text:()=>{},image:value=>seenImages.push(Buffer.from(value.bytes))},[],
    {maxExplicitObservations:2});
  try {
    const first=await caller.input('save',[0,0],'click',[]);
    assert.deepEqual(seenImages[0],await readFile(join(frames,'006.png')));
    await caller.review(first.attempt,{task:'calc-save',phase:'format-dialog',
      reason:'Attribute the retained initial image showing the dialog transition unresolved.'});

    const painted=await caller.observe();
    assert.deepEqual(seenImages[1],await readFile(join(frames,'007.png')));
    await caller.review(painted.attempt,{task:'calc-save',phase:'dialog-review',
      reason:'Attribute the retained fully painted format dialog before choosing confirmation.'});

    const confirmed=await caller.input('confirm',[0,0],'click',[]);
    assert.deepEqual(seenImages[2],await readFile(join(frames,'008.png')));
    await caller.review(confirmed.attempt,{task:'calc-save',phase:'post-confirmation',
      reason:'Attribute the retained stale dialog image; task completion remains unresolved.'});

    const recovered=await caller.observe();
    assert.deepEqual(seenImages[3],await readFile(join(frames,'009.png')));
    await caller.review(recovered.attempt,{task:'calc-save',phase:'recovery-view',
      reason:'Attribute the retained worksheet image after explicit observe-only recovery.'});

    assert.equal(host.state().attempts,4);
    assert.equal(seenImages.length,4);
    assert.equal(caller.state().stopped,null);
    const requests=(await readFile(join(evidence,'host-events.jsonl'),'utf8')).trim()
      .split('\n').map(JSON.parse).filter(row=>row.kind==='send_requested');
    assert.deepEqual(requests.map(row=>row.tool),tools);
    assert.equal(requests.filter(row=>row.tool==='interface_guarded_input').length,2,
      'each input occurs once; neither the stale observation nor recovery view replays it');
    await assert.rejects(caller.observe(),/explicit observation budget exhausted/);
    assert.equal(caller.state().stopped,'explicit observation budget exhausted');
    assert.equal(host.state().attempts,4,'budget exhaustion refuses locally before a fifth host request');
    await writeFile(join(evidence,'caller-policy.json'),JSON.stringify({
      max_explicit_observations:2,explicit_observe_calls:3,
      accepted_explicit_observations:2,refused_locally:1,
      host_attempts_after_refusal:host.state().attempts,stopped:caller.state().stopped
    },null,2)+'\n',{flag:'wx'});
    for(let attempt=1;attempt<=4;attempt++){
      const reply=JSON.parse(await readFile(join(evidence,`reply-${attempt}.json`),'utf8'));
      const meta=JSON.parse(reply.result.content.find(row=>row.type==='text').text);
      assert.equal(meta.task_success,null,'program/cue output never becomes independent task success');
      const review=JSON.parse(await readFile(join(evidence,`review-${attempt}.json`),'utf8'));
      assert.equal(review.source_sequence,attempt+5);
      assert.equal(review.observation_id,'o'+(attempt+5));
    }
  } finally {
    await host.close();
  }
  if(process.env.HANDOFF_REPLAY_CAPTURE){
    const capture=process.env.HANDOFF_REPLAY_CAPTURE;
    await mkdir(capture);
    for(const name of await readdir(evidence))
      await copyFile(join(evidence,name),join(capture,name));
  }
});
