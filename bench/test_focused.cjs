const fs=require('fs'),vm=require('vm');
const variant=process.argv[2]||'original';const {harness,html}=require('./run_app.cjs');
const checks=[];
function check(name,ok,got,expected){checks.push({name,pass:!!ok,got,expected})}
const finite=x=>typeof x==='number'&&Number.isFinite(x);
for(const r of JSON.parse(fs.readFileSync('normal-reference.json','utf8'))){const {c}=harness();const p=c.pz(r.z);check('normal_p::'+r.z,finite(p)&&Math.abs(p-r.p)<=1e-9,p,r.p)}
const triangle='A,B,.2,.1\nB,C,.3,.2\nA,C,.6,.15\nB,A,-.25,.13';
for(const model of ['FE','DL','PM']){
 for(const [name,text,expected] of [
  ['short','A,B,.2,.1', 'At least 3 valid contrasts are required.'],
  ['disconnected',triangle+'\nD,E,.3,.2','The treatment network is disconnected.'],
  ['multiarm','A,B,.2,.1,s1\nB,C,.3,.2,s1\nA,C,.5,.15,s1','Multi-arm studies are unsupported: correlated contrasts require study covariance.'],
  ['repeated','A,B,.2,.1,s1\nA,B,.3,.2,s1\nA,C,.5,.15,s2','Repeated study IDs are unsupported: enter one independent contrast per study.']]){
  const {c,el}=harness();el('f-model').value=model;c.__almIncoLoad(triangle);let error=null;try{c.__almIncoLoad(text)}catch(e){error=e.message}
  const state=c._almLastInco();check(model+'::'+name+'::reason',state?.status==='refused'&&state.reason===expected,{state,error},expected);
  check(model+'::'+name+'::clear',el('ns-body').innerHTML===''&&el('ns-plot').innerHTML==='',{table:el('ns-body').innerHTML,plot:el('ns-plot').innerHTML},'cleared');
 }
 const {c,el}=harness();el('f-model').value=model;c.__almIncoLoad(triangle+'\nC,D,.7,.11');
 const ns=c._almLastInco().nodeSplit;check(model+'::bridge_membership',ns.length===3&&!ns.some(n=>n.comparison.includes('D')),ns.map(n=>n.comparison),['A vs B','B vs C','A vs C']);
}
for(const [name,a,b,d] of [['quoted','A, comma','B"quote','C'],['pipe','A|B','C','D'],['prototype','__proto__','constructor','toString'],['markup','<b>A</b>','B&C','D']]){
 const {c,el}=harness();const q=s=>'"'+s.replaceAll('"','""')+'"';const input=[[a,b,.2,.1],[b,d,.3,.2],[a,d,.6,.15]].map(r=>r.map(x=>q(String(x))).join(',')).join('\n');
 let error=null;try{c.__almIncoLoad(input)}catch(e){error=e.message}
 const s=c._almLastInco();check(name+'::input',!error&&c.parse(input).length===3&&c.parse(input)[0].A===a,{error,parsed:c.parse(input)},'three exact labeled rows');
 check(name+'::splits',!error&&s?.nodeSplit?.length===3,s?.nodeSplit?.length,3);
 check(name+'::network_keys',!error&&JSON.stringify(Object.keys(s?.estimates||{}).sort())===JSON.stringify([a,b,d].sort()),Object.keys(s?.estimates||{}),[a,b,d]);
 if(name==='markup')check('escaped_markup',!el('ns-body').innerHTML.includes('<b>A</b>')&&el('ns-body').innerHTML.includes('&lt;b&gt;'),el('ns-body').innerHTML,'escaped label');
}
const busScript=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).find(s=>s.includes('ma-comparisons-v1 reader'));
for(const fixture of JSON.parse(fs.readFileSync('bus-reference.json','utf8'))){
 const {c,el}=harness();vm.runInContext(fs.readFileSync(`app-${variant}/shared/ma-comparisons-v1.js`,'utf8'),c);vm.runInContext(busScript,c);
 c.MaComparisons.write(fixture.studies,fixture.measure);el('btn-bus-load').click();const rows=c.parse(el('src').value);
 check('bus_numeric::'+fixture.key+'::count',rows.length===fixture.rows.length,rows.length,fixture.rows.length);
 fixture.rows.forEach((r,i)=>{for(const f of ['A','B'])check('bus_numeric::'+fixture.key+'::'+i+'::'+f,rows[i]?.[f]===r[f],rows[i]?.[f],r[f]);for(const f of ['te','se'])check('bus_numeric::'+fixture.key+'::'+i+'::'+f,finite(rows[i]?.[f])&&Math.abs(rows[i][f]-r[f])<=1e-9*Math.max(1,Math.abs(r[f])),rows[i]?.[f],r[f])});
}
for(const mode of ['empty','HR','RD']){
 const {c,el}=harness();vm.runInContext(fs.readFileSync(`app-${variant}/shared/ma-comparisons-v1.js`,'utf8'),c);vm.runInContext(busScript,c);
 if(mode!=='empty')c.MaComparisons.write([{id:'s1',arms:[{treatment:'A',events:1,n:10},{treatment:'B',events:2,n:10}]}],mode);
 el('btn-bus-load').click();const s=c._almLastInco();check('bus::'+mode+'::cleared',s?.status==='refused'&&el('ns-body').innerHTML===''&&el('ns-plot').innerHTML==='',s,'cleared refusal');
}
for(const measure of ['OR','RR','MD','SMD']){
 for(const multi of [false,true]){
  const {c,el}=harness();vm.runInContext(fs.readFileSync(`app-${variant}/shared/ma-comparisons-v1.js`,'utf8'),c);vm.runInContext(busScript,c);
  const arm=(t,mean)=>({treatment:t,events:10+mean,n:50,mean,sd:2});
  const studies=[{id:'s1',arms:[arm('A',2),arm('B',3),...(multi?[arm('C',4)]:[])]},{id:'s2',arms:[arm('B',2),arm('C',3)]},{id:'s3',arms:[arm('A',2),arm('C',4)]}];
  c.MaComparisons.write(studies,measure);let error=null;try{el('btn-bus-load').click()}catch(e){error=e.message}
  const state=c._almLastInco();
  check('bus::'+measure+'::'+(multi?'multiarm_refusal':'twoarm'),!error&&(multi?state?.status==='refused':state?.nodeSplit?.length===3),{error,state},multi?'explicit refusal':'three computed splits');
 }
}
const passed=checks.filter(x=>x.pass).length;fs.writeFileSync(`focused-${variant}.json`,JSON.stringify({passed,checks:checks.length,results:checks},null,2)+'\n');
console.log(`${passed}/${checks.length} focused checks pass (${variant}; Node, not browser)`);
