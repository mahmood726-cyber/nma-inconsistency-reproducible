// Execute the shipped pure JavaScript engine and renderer with a minimal DOM.
// This is not a browser or layout test. No statistical implementation is replaced.
const fs=require('fs'),vm=require('vm'),path=require('path');
const variant=process.argv[2]||'original';
const html=fs.readFileSync(`app-${variant}/nma-inconsistency/index.html`,'utf8');
const main=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).find(s=>s.includes('function fitNMA('));
if(!main)throw Error('No shipped engine');
function harness(){
 const elements=new Map(),downloads=[];
 function el(id){if(!elements.has(id))elements.set(id,{id,value:'',innerHTML:'',get textContent(){return this.innerHTML.replace(/<[^>]*>/g,'')},set textContent(v){this.innerHTML=String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')},attrs:{},listeners:{},style:{},setAttribute(k,v){this.attrs[k]=v},getAttribute(k){return this.attrs[k]},addEventListener(k,f){this.listeners[k]=f},appendChild(){},removeChild(){},querySelector(q){return el(id+' '+q)},click(){if(this.listeners.click)return this.listeners.click();if(this.href)downloads.push({name:this.download,blob:this.href});}});return elements.get(id)}
 const selectors={h1:html.match(/<h1>([\s\S]*?)<\/h1>/)?.[1], 'header p':html.match(/<header>[\s\S]*?<p>([\s\S]*?)<\/p>/)?.[1],footer:html.match(/<footer>([\s\S]*?)<\/footer>/)?.[1]};
 const document={readyState:'complete',getElementById:id=>elements.get(id)||null,createElement:t=>el('created'+elements.size+t),head:el('head'),body:el('body'),querySelector:s=>{if(selectors[s]!=null){el(s).innerHTML=selectors[s];return el(s)}return null},title:'NMA Inconsistency'};
 for(const id of ['src','f-model','ns-body','ns-plot','dbt','btn-run'])el(id);
 el('src').dispatchEvent=()=>{};el('btn-run').insertAdjacentElement=(_,node)=>elements.set(node.id,node);
 const storage=new Map();
 const c={document,console,Blob,Event:class Event{},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)},URL:{createObjectURL:b=>b,revokeObjectURL(){}},setTimeout:()=>0,window:null};c.window=c;
 vm.createContext(c);el('src').value=html.match(/<textarea[^>]*id="src"[^>]*>([\s\S]*?)<\/textarea>/)[1];el('f-model').value='FE';
 vm.runInContext(main,c,{timeout:60000});
 vm.runInContext(fs.readFileSync(`app-${variant}/hub/shared/results-export.js`,'utf8'),c);
 c.alm.resultsExport({target:el('exports'),getResults:()=>c._almLastInco(),basename:'nma-inconsistency'});
 return {c,el,downloads};
}
async function run(){
 const corpus=JSON.parse(fs.readFileSync('corpus.json','utf8')),out=[];
 for(const conf of corpus){
  const {c,el,downloads}=harness();el('f-model').value=conf.model;
  const quote=s=>/[",\r\n]/.test(String(s))?'"'+String(s).replaceAll('"','""')+'"':String(s);
  const text=conf.rows.map(r=>[r.A,r.B,r.te,r.se,r.study].map(quote).join(',')).join('\n');
  let error=null;try{c.__almIncoLoad(text)}catch(e){error=String(e.message)}
  const state=JSON.parse(JSON.stringify(c._almLastInco()));
  const parsed=c.parse(text);let supplemental=null;
  try{supplemental=c.nodeSplit(parsed,undefined,state?.tau2)}catch(e){}
  for(const action of ['json','csv','md','report-md','report-txt'])await el(`exports [data-action="${action}"]`).click();
  const exports={};for(const d of downloads)exports[d.name]=await d.blob.text();
  out.push({key:conf.key,error,state,parsed,supplemental,table:el('ns-body').innerHTML,global:el('dbt').innerHTML,svg:el('ns-plot').innerHTML,viewBox:el('ns-plot').attrs.viewBox,exports});
 }
 fs.writeFileSync(`app-${variant}.json`,JSON.stringify(out,null,2)+'\n');
 console.log(`${out.length} shipped-page configurations captured in Node ${process.version} (${variant}); browser layout untested`);
}
module.exports={harness,html};
if(require.main===module)run().catch(e=>{console.error(e);process.exit(1)});
