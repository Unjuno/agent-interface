const fs=require("node:fs");
const mode=process.argv[2];
const input=JSON.parse(fs.readFileSync("/src/fixture.json","utf8"));
if(mode==="candidate"){
 const candidate=eval("(" + fs.readFileSync("/src/candidate.js","utf8") + ")");
 const report=candidate(input);
 fs.writeFileSync("/out/candidate.raw.json",JSON.stringify(report,null,2)+"\n");
 process.stdout.write(JSON.stringify({mode,allocation:report.allocation,rows:report.rows.length,
   eligible_weight:report.eligible_weight,observation_rate:report.observation_rate})+"\n");
}else if(mode==="audit"){
 const report=JSON.parse(fs.readFileSync("/input/candidate.raw.json","utf8"));
 const auditor=eval("(" + fs.readFileSync("/src/auditor.js","utf8") + ")");
 const result=auditor(input,report);
 fs.writeFileSync("/out/audit.raw.json",JSON.stringify(result,null,2)+"\n");
 process.stdout.write(JSON.stringify({mode,allocation:result.allocation,base_audit:result.base_audit,
   expected_rows:result.expected_rows,observed_rows:result.observed_rows,mutation_count:result.mutation_count,
   rejected_mutations:result.mutations.filter(x=>x.rejected).length})+"\n");
 if(!result.base_audit||result.mutations.some(x=>!x.rejected))process.exitCode=1;
}else throw new Error("mode must be candidate or audit");
