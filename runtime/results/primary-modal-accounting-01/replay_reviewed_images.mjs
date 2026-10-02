/** Recorded-reply integration replay; no GUI, model review or live input. */
import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';
import {createInterface} from 'node:readline';
import assert from 'node:assert/strict';
import {createInstrumentedRelayClient} from '../../host_v1/relay_host.mjs';
import {createPrimaryExchange} from '../../host_v1/primary_exchange.mjs';
const root=dirname(fileURLToPath(import.meta.url));
const source=join(root,'..','primary-target-tools-live-04','case');
const read=async path=>JSON.parse(await readFile(path,'utf8'));
if(process.argv[2]==='fixture') {
  const rl=createInterface({input:process.stdin}); let expected=1;
  for await(const line of rl) {
    const request=JSON.parse(line);
    assert.deepEqual(request,await read(join(source,'host',`request-${expected}.json`)));
    const reply=await read(join(source,'host',`reply-${expected}.json`));
    console.log(JSON.stringify(reply)); expected++;
  }
  assert.equal(expected,8);
} else {
  const output=join(root,'recorded-reply-reuse-01'); await mkdir(output);
  const summaries=[];
  for(const reuseReviewedImages of [false,true]) {
    const arm=join(output,reuseReviewedImages?'reuse':'full'); await mkdir(arm);
    const host=await createInstrumentedRelayClient({command:process.execPath,
      args:[fileURLToPath(import.meta.url),'fixture'],evidenceDirectory:join(arm,'host'),reuseReviewedImages});
    const exchange=await createPrimaryExchange({host,directory:join(arm,'exchange'),route:'direct-post',
      options:{observationArguments:{target:'app',frame:'screen_physical_px',region:[0,0,1280,800],compact:true,report_refs:true}}});
    let images=0;const references=[];const outputs=[];
    try {
      for(let id=1;id<=13;id++) {
        const command=await read(join(source,'exchange',`request-${id}.json`));
        if(['review','acknowledgeText'].includes(command.method)) {
          command.args[1]={...command.args[1],task:'recorded-reply-contract-only',
            reason:'Automated retained-reply contract replay; not a current model review or live task result.'};
        }
        const result=await exchange.execute(command);outputs.push(result);
        images+=result.images.length;
        const markers=result.presented_text.filter(x=>x?.schema==='agent-interface/reviewed-image-reference-v1');
        for(const marker of markers) references.push({command:id,...marker});
      }
    } finally {await host.close();}
    assert.equal(host.state().attempts,7);
    assert.equal(images,reuseReviewedImages?3:5);
    assert.deepEqual(references.map(x=>[x.command,x.attempt,x.base_attempt]),reuseReviewedImages?[[7,4,3],[9,5,3]]:[]);
    for(const ref of references) {
      assert.equal(ref.image_sha256,'4999b53fb2f493dd7e0d6ca06b1d53a47db007ce07ba423275733b1b4d7957d9');
      assert.equal(ref.base_reply_sha256,outputs[4].presented_text.find(x=>x?.schema==='agent-interface/reviewed-image-reference-v1')?.reply_sha256??ref.base_reply_sha256);
      // Current selection metadata is still independently presented.
      const current=outputs[ref.command-1].presented_text.filter(x=>typeof x==='string').map(x=>JSON.parse(x));
      assert.ok(current.some(x=>ref.command===9?x.binding_revision===2:typeof x.review_request==='object'));
    }
    assert.equal(outputs[10].images.length,1); // Changed final PNG cannot reuse modal pixels.
    for(let attempt=1;attempt<=7;attempt++) {
      assert.deepEqual(await read(join(arm,'host',`reply-${attempt}.json`)),await read(join(source,'host',`reply-${attempt}.json`)));
    }
    summaries.push({reuseReviewedImages,public_requests:7,primary_commands:13,image_callbacks:images,
      references,original_reply_equality:true,scope:'Automated recorded-reply contract only; no model-visible/token/latency/live correctness benefit measured.'});
  }
  await writeFile(join(root,'recorded-reply-reuse.json'),JSON.stringify({status:'PASS_RECORDED_REPLY_INTEGRATION',arms:summaries},null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({status:'PASS_RECORDED_REPLY_INTEGRATION',image_callbacks:summaries.map(x=>x.image_callbacks)}));
}