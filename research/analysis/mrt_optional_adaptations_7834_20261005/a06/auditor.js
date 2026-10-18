const fs=require("fs"), f=JSON.parse(fs.readFileSync("./fixture.json","utf8")), got=JSON.parse(fs.readFileSync(process.env.CANDIDATE_PATH||"/input/candidate.json","utf8"));
const expectedRows=[];
for(const m of ["M0","M1"]){const p=f.treatment_propensity[m];expectedRows.push({m,a:0,prob:1-p,p1:p,y:f.potential_outcomes[m]["0"]});expectedRows.push({m,a:1,prob:p,p1:p,y:f.potential_outcomes[m]["1"]})}
function sameRows(a,b){if(!Array.isArray(a)||a.length!==b.length)return false;const keys=["m","a","prob","p1","y"];const canon=r=>{if(!r||Object.keys(r).sort().join(",")!==keys.slice().sort().join(","))return null;return JSON.stringify(keys.map(k=>r[k]))};const x=a.map(canon).sort(),y=b.map(canon).sort();return x.every((v,i)=>v!==null&&v===y[i])}
const oracle={M0:f.potential_outcomes.M0["1"]-f.potential_outcomes.M0["0"],M1:f.potential_outcomes.M1["1"]-f.potential_outcomes.M1["0"]};
const pooled=.5*oracle.M0+.5*oracle.M1,heterogeneity=oracle.M0-oracle.M1;
const close=(x,y)=>Number.isFinite(x)&&Math.abs(x-y)<1e-12;
const variants=[x=>x.pop(),x=>x[0]={...x[0],m:"M1"},x=>x[0]={...x[0],a:1},x=>x[0]={...x[0],prob:x[0].prob+0.1},x=>x[0]={...x[0],p1:0.5},x=>x[0]={...x[0],y:x[0].y+1},x=>x[0]={...x[0],extra:true}];
let rejected=0;for(const mutate of variants){const x=JSON.parse(JSON.stringify(got.rows));mutate(x);if(!sameRows(x,expectedRows))rejected++}
const gateStatuses=f.controls.map(c=>c.timing==="pre-treatment"&&Number.isFinite(c.p)&&c.p>0&&c.p<1?"IDENTIFIABLE":"NONIDENTIFIABLE");
const controlMatch=JSON.stringify(got.controls)===JSON.stringify(f.controls.map((c,i)=>({id:c.id,status:gateStatuses[i]})));
const audit=sameRows(got.rows,expectedRows)&&close(got.effects.M0,oracle.M0)&&close(got.effects.M1,oracle.M1)&&close(got.pooled,pooled)&&close(got.heterogeneity,heterogeneity)&&controlMatch;
console.log(JSON.stringify({audit,rows:expectedRows.length,oracle,pooled,heterogeneity,mutations_rejected:rejected,mutations_total:variants.length,nonidentifiable_count:gateStatuses.filter(x=>x==="NONIDENTIFIABLE").length,controls:gateStatuses}));
