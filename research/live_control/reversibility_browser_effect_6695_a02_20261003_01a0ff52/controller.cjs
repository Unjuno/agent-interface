/* Controller reads only visible form feedback. No truth/config files or effect ledger. */
const fs=require('fs');
const {chromium}=require(process.env.PLAYWRIGHT_ROOT);
async function main(){
 const [origin,scheduleFile,outputFile]=process.argv.slice(2);
 const schedule=JSON.parse(fs.readFileSync(scheduleFile,'utf8'));
 if(!process.env.CHROMIUM_EXE)throw Error('fixed CHROMIUM_EXE required');
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXE,headless:true,args:['--disable-gpu','--disable-background-networking']});
 let failed=false;const rows=[];
 try{
  for(const trial of schedule){
   const context=await browser.newContext({viewport:{width:800,height:600},serviceWorkers:'block'});
   let blocked=0;await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():(blocked++,r.abort()));
   const page=await context.newPage();page.setDefaultTimeout(5000);
   const row={trial_id:trial.trial_id,case_id:trial.case_id,policy:trial.policy,status:null,signal:null,error:null,blocked_external_requests:0};
   try{
    await page.goto(origin+'/?trial='+encodeURIComponent(trial.trial_id));
    await page.locator('#start').click();
    await page.waitForFunction(()=>document.getElementById('state').textContent==='STARTED');
    if(trial.policy==='STAGE')await page.locator('#prepare').click();
    await page.waitForFunction(()=>document.getElementById('signal').textContent!=='PENDING');
    const signal=await page.locator('#signal').textContent();row.signal=signal;
    const target=signal==='B'?'B':'A';
    if(trial.policy==='WAIT'){
     await page.locator('#target').selectOption(target);await page.locator('#prepare').click();
    }
    await page.waitForFunction(()=>document.getElementById('state').textContent==='READY');
    if(trial.policy==='STAGE'&&target==='B'){
     await page.locator('#target').selectOption('B');await page.locator('#edit').click();
     await page.waitForFunction(()=>document.getElementById('state').textContent==='READY');
    }
    await page.locator('#commit').click();
    await page.waitForFunction(()=>['COMMITTED','DEADLINE'].includes(document.getElementById('state').textContent));
    row.status=await page.locator('#state').textContent();
   }catch(error){row.error=String(error);failed=true;}
   finally{row.blocked_external_requests=blocked;rows.push(row);await context.close();}
   fs.appendFileSync(outputFile,JSON.stringify(row)+'\n',{flag:'a'});
   if(failed)break;
  }
 }finally{await browser.close();}
 console.log(JSON.stringify({rows:rows.length,failed,browser:'closed',browser_version:browser.version()}));
 if(failed)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
