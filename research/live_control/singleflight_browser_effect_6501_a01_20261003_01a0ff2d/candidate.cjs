'use strict';
const fs=require('fs'), path=require('path');
const {chromium}=require('playwright');
const {Broker,identity,admit}=require('./broker.cjs');
const hr=()=>process.hrtime.bigint();
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function main() {
  const [origin,output,mode]=process.argv.slice(2);
  if(new URL(origin).hostname!=='127.0.0.1')throw Error('private loopback origin required');
  const config=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures.json')));
  const post=async(endpoint,body={})=>{
    const r=await fetch(origin+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body),signal:AbortSignal.timeout(12000)});
    if(!r.ok)throw Error('fixture request failed:'+endpoint+':'+r.status);
    return r.json();
  };
  const status=async()=> (await fetch(origin+'/barrier',{signal:AbortSignal.timeout(12000)})).json();
  let bserver, browser;
  const watchdog=setTimeout(()=>{
    raw.watchdog_fired=true;
    if(bserver)bserver.kill().catch(()=>{});
  },135000);
  const raw={schema:'6501-browser-client-v1',node:process.version,started_utc:new Date().toISOString(),
    clock:'process.hrtime.bigint nanoseconds; comparable only inside this process',rows:[],cleanup:{}};
  let fatal=null;
  try {
    bserver=await chromium.launchServer({executablePath:process.env.STUDY_CHROME,headless:true,
      args:['--disable-gpu','--disable-background-networking','--disable-component-update',
        '--disable-extensions','--no-first-run','--no-default-browser-check']});
    raw.browser_pid=bserver.process().pid;
    browser=await chromium.connect(bserver.wsEndpoint());
    raw.browser_version=browser.version();
    const orders=mode==='mini' ? [['cold_equivalent','independent'],['cold_equivalent','scoped'],
      ['mixed_targets','predicate'],['mixed_targets','scoped'],
      ['generation_change','predicate'],['generation_change','scoped']] : config.orders;
    for(const [caseId,policy] of orders) {
      const fixture=config.cases.find(c=>c.id===caseId);
      await post('/setup',{case:caseId,policy});
      const context=await browser.newContext({viewport:{width:900,height:700}});
      await context.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
      const page=await context.newPage(); page.setDefaultTimeout(5000);
      const events=[];
      const emit=event=>events.push({...event,seq:events.length,ns:String(hr())});
      const row={case:caseId,policy,events,consumers:[],warmup:null};
      try {
        await page.goto(origin+'/');
        await page.locator('#commit-w1').waitFor();
        async function scope(target) {
          const source=await page.locator('#source').getAttribute('data-source');
          const generationText=await page.locator('#target-'+target).getAttribute('data-generation');
          const text=await page.locator('#target-'+target).textContent();
          if(!/^[1-9][0-9]*$/.test(generationText)||text!==target+': READY')throw Error('public DOM scope unavailable');
          const generation=Number(generationText);
          if(!Number.isSafeInteger(generation))throw Error('invalid generation');
          return {verifier:'dom-ready-v1',source,target,generation,
            digest:`${source}/${target}/${generation}/READY`,predicate:'ready',window:source,role:'read_only'};
        }
        const broker=new Broker(policy,emit);
        const read=(observed,phase)=>post('/read',{target:observed.target,phase,snapshot:observed});
        if(fixture.warm) {
          const observed=await scope('A');
          row.warmup=await broker.get(observed,()=>read(observed,'warmup'));
          emit({event:'warmup_complete',read_id:row.warmup.read_id});
        }
        let actionLane=Promise.resolve();
        function consume(request,observed) {
          const started=hr(),deadline=started+BigInt(config.waiter_deadline_ms)*1000000n;
          emit({event:'waiter_start',request,scope:observed,deadline_ns:String(deadline)});
          const descriptive=broker.get(observed,()=>read(observed,'offered'));
          return descriptive.then(result=>{
            emit({event:'delivered',request,read_id:result.read_id,scope:result.scope});
            const action=actionLane.then(async()=>{
              const current=await scope(fixture.targets[request]);
              const decisionNs=hr();
              const decision=admit(result,observed,current,decisionNs,deadline);
              emit({event:'decision',request,decision,requested:observed,current,
                read_id:result.read_id,ns_decision:String(decisionNs)});
              let feedback=null;
              if(decision==='ELIGIBLE') {
                // Own per-request UI capability, never the common read's authority.
                await page.locator('#evidence-'+request).fill(result.evidence_ref);
                await page.locator('#commit-'+request).click();
                await page.locator('#result-'+request).filter({hasText:'Committed'}).waitFor();
                feedback=await page.locator('#result-'+request).textContent();
                emit({event:'useful_feedback',request,text:feedback});
              }
              const ended=hr();
              return {request,requested:observed,result,current,decision,feedback,
                started_ns:String(started),deadline_ns:String(deadline),decision_ns:String(decisionNs),
                ended_ns:String(ended),elapsed_ns:String(ended-started)};
            });
            actionLane=action.catch(()=>{});
            return action;
          });
        }
        const offered=hr(); row.offered_ns=String(offered);
        const firstScope=await scope(fixture.targets.w1);
        const secondScope=['generation','late'].includes(fixture.kind)?null:await scope(fixture.targets.w2);
        const first=consume('w1',firstScope);
        let second;
        if(fixture.kind==='late') {
          await post('/release');
          row.consumers.push(await first);
          emit({event:'late_caller_after_completion'});
          second=consume('w2',await scope(fixture.targets.w2));
          row.consumers.push(await second);
        } else {
          if(fixture.kind==='generation') {
            const limit=Date.now()+5000;
            while((await status()).reads===0){if(Date.now()>=limit)throw Error('first read barrier missing');await pause(5);}
            await page.locator('#flip').click();
            await page.locator('#generation').filter({hasText:'2'}).waitFor();
            emit({event:'public_generation_change'});
          }
          second=consume('w2',secondScope||await scope(fixture.targets.w2));
          // Same external service-release schedule for every policy. Both callers registered.
          await post('/release');
          row.consumers.push(...await Promise.all([first,second]));
        }
        await actionLane;
        row.ended_ns=String(hr()); row.elapsed_ns=String(BigInt(row.ended_ns)-offered);
        row.pending_entries=broker.pending.size;
        if(mode!=='mini' && caseId==='cold_equivalent' && policy==='scoped')
          await page.screenshot({path:path.join(path.dirname(output),'fixture-effect.png')});
        row.status='COMPLETE';
      } catch(error) {
        row.status='ERROR';row.error=String(error);
        await post('/release').catch(()=>{});
        throw error;
      } finally {
        await context.close();
        row.context_closed=true;raw.rows.push(row);
      }
    }
  } catch(error) {fatal=String(error);raw.fatal=fatal;}
  finally {
    clearTimeout(watchdog);
    if(browser)await browser.close().catch(error=>{raw.cleanup.browser_close_error=String(error);});
    if(bserver) {
      await bserver.close().catch(error=>{raw.cleanup.server_close_error=String(error);});
      raw.cleanup.browser_exit_code=bserver.process().exitCode;
      raw.cleanup.browser_signal=bserver.process().signalCode;
      raw.cleanup.browser_closed=bserver.process().exitCode!==null || bserver.process().signalCode!==null;
    }
    raw.ended_utc=new Date().toISOString();
    fs.writeFileSync(output,JSON.stringify(raw,null,2)+'\n',{flag:'wx'});
  }
  console.log(JSON.stringify({rows:raw.rows.length,fatal,cleanup:raw.cleanup}));
  if(fatal)process.exitCode=1;
}
main().catch(error=>{console.error(error);process.exitCode=1;});
