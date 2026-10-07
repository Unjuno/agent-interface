const fs=require("fs");
const f=JSON.parse(fs.readFileSync("./fixture.json","utf8")); const candidate=JSON.parse(fs.readFileSync("/input/candidate.json","utf8"));
const expected=[]; for(const m of ["M0","M1"]){const p=f.treatment_propensity[m],y0=f.potential_outcomes[m]["0"],y1=f.potential_outcomes[m]["1"]; expected.push({m,a:0,prob:1-p,p1:p,y:y0},{m,a:1,prob:p,p1:p,y:y1});}
function close(a,b){return Number.isFinite(a)&&Math.abs(a-b)<1e-12}
function eqRows(got,want){if(!Array.isArray(got)||got.length!==want.length)return false;const key=r=>JSON.stringify([r.m,r.a,r.prob,r.p1,r.y]);return [...got].map(key).sort().join("|")===[...want].map(key).sort().join("|")}
function estimate(rows,m){const rr=rows.filter(r=>r.m===m),n=rr.length;if(!n)return null;let tr=0,co=0;for(const r of rr){if(r.a===1)tr+=r.prob*r.y/r.p1/n;else co+=r.prob*r.y/(1-r.p1)/n;}return tr-co}
const effect={M0:estimate(expected,"M0"),M1:estimate(expected,"M1")},pooled=(effect.M0+effect.M1)/2;
const mutations=[x=>x.rows.pop(),x=>x.rows[0]={...x.rows[0],m:"M1"},x=>x.rows[0]={...x.rows[0],a:1},x=>x.rows[0]={...x.rows[0],prob:x.rows[0].prob+0.1},x=>x.rows[0]={...x.rows[0],p1:0.5},x=>x.rows[0]={...x.rows[0],y:x.rows[0].y+1},x=>x.rows[0]={...x.rows[0],extra:"unexpected"}];
let rejected=0;for(const mutate of mutations){const x=JSON.parse(JSON.stringify(candidate));mutate(x);if(!eqRows(x.rows,expected))rejected++}
function identifiable(p,timing="pre-treatment"){return timing==="pre-treatment"&&Number.isFinite(p)&&p>0&&p<1}
const gates=[!identifiable(0,"pre-treatment"),!identifiable(0.25,"post-treatment"),!identifiable(null,"pre-treatment")];
console.log(JSON.stringify({audit:eqRows(candidate.rows,expected)&&close(candidate.effects.M0,effect.M0)&&close(candidate.effects.M1,effect.M1)&&close(candidate.pooled,pooled)&&close(candidate.heterogeneity,effect.M0-effect.M1),rows:expected.length,oracle:effect,pooled,heterogeneity:effect.M0-effect.M1,mutations_rejected:rejected,mutations_total:mutations.length,nonidentifiable:gates,nonidentifiable_count:gates.filter(Boolean).length}));
