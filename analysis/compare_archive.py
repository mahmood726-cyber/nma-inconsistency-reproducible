# Generated from bench/compare.py; only input/output paths differ (see analysis/compare_archive.diff).
import json,sys,math,re,csv,io,html
from pathlib import Path
from collections import Counter
from decimal import Decimal,ROUND_HALF_UP
import lzma
ROOT=Path(__file__).resolve().parents[1]
variant,REFDIR,OUTDIR=sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3])
assert variant in ('original','patched')
corpus=json.loads((ROOT/'data/corpus.json').read_text(encoding='utf-8'))
if variant == 'patched':
    # Never fall back to historical outputs when the fresh capture is absent.
    apps=json.loads((OUTDIR/'capture/app-patched.json').read_text(encoding='utf-8'))
else:
    apps=json.loads(lzma.decompress((ROOT/f'results/app-{variant}.json.xz').read_bytes()).decode('utf-8'))
refs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(REFDIR.glob('*.json'))]
stats={};failures=[]; checks=[]
def check(q,key,ok,diff=0,tol=0,got=None,expected=None,category='numerical'):
    st=stats.setdefault(q,dict(checks=0,passed=0,max_difference=0,tolerance=tol,category=category))
    if tol not in st.setdefault('tolerances',[]):st['tolerances'].append(tol)
    st['checks']+=1;st['passed']+=bool(ok)
    if math.isfinite(diff):st['max_difference']=max(st['max_difference'],diff)
    else:st['invalid_evidence']=st.get('invalid_evidence',0)+1
    if not ok: failures.append(dict(quantity=q,key=key,got=got,expected=expected,difference=diff if math.isfinite(diff) else None,tolerance=tol))
def exact(q,key,a,b,category='contract'):
    check(q,key,a==b,0 if a==b else 1,got=a,expected=b,category=category)
def num(q,key,a,b,tol=1e-9,absolute=False,category='numerical'):
    if b is None:
        exact(q+'_undefined',key,a,None);return
    ok=isinstance(a,(float,int)) and not isinstance(a,bool) and math.isfinite(a) and isinstance(b,(float,int)) and math.isfinite(b)
    diff=(abs(a-b)/(1 if absolute else max(1,abs(b)))) if ok else math.inf
    check(q,key,ok and diff<=tol,diff,tol,got=a,expected=b,category=category)
def index(rows,name):
    ks=[r['key'] for r in rows];exact(name+'_unique','ALL',len(ks),len(set(ks)),'coverage')
    exact(name+'_coverage','ALL',sorted(ks),sorted(c['key'] for c in corpus),'coverage')
    return {r['key']:r for r in rows}
app=index(apps,'app');ref=index(refs,'reference');exact('corpus_unique','ALL',len(corpus),len({c['key'] for c in corpus}),'coverage')
def fmt(x,d=3):
    if x is None or not math.isfinite(x):return '\u2014'
    if x==0:x=0.0
    return str(Decimal.from_float(float(x)).quantize(Decimal(1).scaleb(-d),rounding=ROUND_HALF_UP))
for c in corpus:
    k=c['key'];a=app.get(k);r=ref.get(k)
    exact('app_evidence',k,a is not None,True,'coverage');exact('reference_evidence',k,r is not None,True,'coverage')
    if a is None or r is None:continue
    exact('reference_valid',k,r['status'] in ['ok','refused'],True,'coverage')
    if r['status'] not in ['ok','refused']:continue
    state=a.get('state') or {};status=state.get('status','ok')
    exact('input_status',k,status,r['status'],'refusal' if r['status']=='refused' else 'contract')
    exact('execution_error',k,a['error'],None)
    # Capture the actual shipped download serializer, not a surrogate export.
    exports=a.get('exports',{});raw=exports.get('nma-inconsistency.json')
    try: exported=json.loads(raw)
    except Exception:exported=None
    exact('json_export',k,exported,state,'export')
    if r['status']=='refused':
        exact('refusal_reason',k,state.get('reason'),r['reason'],'refusal')
        exact('refusal_table_clear',k,a['table'],'','refusal');exact('refusal_plot_clear',k,a['svg'],'','refusal')
        continue
    if status!='ok':continue
    expected_rows=[{x:r0[x] for x in ['A','B','te','se']} for r0 in c['rows']]
    parsed=[{x:r0[x] for x in ['A','B','te','se']} for r0 in a['parsed']]
    exact('parsed_rows',k,parsed,expected_rows)
    exact('input_k',k,len(a['parsed']),r['k']);exact('model',k,state.get('model'),c['model']);exact('treatment_membership',k,state.get('trts'),r['trts'])
    tol=1e-6 if c['model']=='PM' else 1e-9
    for q in ['tau2','Qrandom']:num(q,k,state.get(q),r.get(q),tol)
    num('Q',k,state.get('Q'),r.get('Q'));exact('df',k,state.get('df'),r.get('df'))
    for field in ['estimates','estimatesRandom']:
        for t,v in r[field].items():
            for q in ['est','se']:num(field+'_'+q,k+'::'+t,state.get(field,{}).get(t,{}).get(q),v[q],tol if field.endswith('Random') else 1e-9)
    g=state.get('dbt',{})
    num('dbt_Q',k,g.get('Q'),r['dbt']['Q'],tol);exact('dbt_df',k,g.get('df'),r['dbt']['df']);num('dbt_p',k,g.get('p'),r['dbt']['p'],absolute=True)
    ns=state.get('nodeSplit',[]);names=[n['comparison'] for n in ns];rn={n['comparison']:n for n in r['nodeSplit']}
    exact('split_unique',k,len(names),len(set(names)));exact('split_membership',k,sorted(names),sorted(rn))
    sn={n['comparison']:n for n in ns};supp={n['comparison']:n for n in a.get('supplemental') or []}
    for pair,rr in rn.items():
        aa=sn.get(pair,{});kk=k+'::'+pair
        for part in ['direct','indirect']:
            for q in ['mean','se']:num(part+'_'+q,kk,aa.get(part,{}).get(q),rr[part][q],tol)
        for q in ['diff','seDiff','z','p']:num('split_'+q,kk,aa.get(q),rr[q],1e-9 if q=='p' else tol,absolute=q=='p')
        exact('direct_k',kk,supp.get(pair,{}).get('kDirect'),rr['kDirect'])
    # Rendered text strings vs serialized full-precision values, including signs.
    trs=re.findall(r'<tr>(.*?)</tr>',a['table'],re.S)
    exact('table_row_count',k,len(trs),len(ns),'display')
    for i,n in enumerate(ns):
        if i>=len(trs):break
        cells=[html.unescape(re.sub('<[^>]+>','',s)).strip() for s in re.findall(r'<td>(.*?)</td>',trs[i],re.S)]
        exp=[n['comparison'],fmt(n['direct']['mean'])+' ('+fmt(n['direct']['se'])+')',fmt(n['indirect']['mean'])+' ('+fmt(n['indirect']['se'])+')',fmt(n['diff'])+' ('+fmt(n['seDiff'])+')',fmt(n['z'],2),fmt(n['p']), 'inconsistent' if n['p'] is not None and n['p']<.05 else 'consistent']
        exact('display_split',k+'::'+n['comparison'],cells,exp,'display')
    codes=[html.unescape(s) for s in re.findall(r'<code>(.*?)</code>',a['global'])]
    exact('display_global',k,codes,[fmt(g.get('Q'),2),str(g.get('df')),fmt(g.get('p'))],'display')
    model_text='fixed-effect (\u03c4\u00b2=0)' if c['model']=='FE' else c['model']+' \u03c4\u00b2 = '+fmt(state.get('tau2'),4)
    exact('display_model_tau',k,'Model: '+model_text+'.' in a['global'],True,'display')
    if g.get('p') is None:exact('untestable_label',k,'inconsistency is not testable' in a['global'],True,'display')
    # CSV/data Markdown exports: every flattened key is checked against JSON.
    def flatten(obj,prefix=''):
        out={}
        for key,v in obj.items():
            key=prefix+'.'+key if prefix else key
            if isinstance(v,dict):out.update(flatten(v,key))
            else:out[key]=v
        return out
    flat=flatten(state)
    try: csvrows=list(csv.reader(io.StringIO(exports['nma-inconsistency.csv'])));csvdict=dict(csvrows[1:])
    except Exception:csvrows=[];csvdict={}
    exact('csv_keys',k,sorted(csvdict),sorted(flat),'export')
    for key,v in flat.items():
        got=csvdict.get(key)
        if isinstance(v,list):
            try:cv=json.loads(got)
            except Exception:cv=None
            exact('csv_array',k+'::'+key,cv,v,'export')
        elif isinstance(v,(int,float)):num('csv_number',k+'::'+key,float(got) if got is not None else None,v,0,category='export')
        else:exact('csv_scalar',k+'::'+key,got,'' if v is None else str(v),'export')
    for file in ['nma-inconsistency.md','nma-inconsistency-report.md','nma-inconsistency-report.txt']:
        exact('text_export_present',k+'::'+file,bool(exports.get(file)),True,'export')
    markdown=exports.get('nma-inconsistency.md','')
    mdrows=[re.split(r'(?<!\\)\|',line)[1:-1] for line in markdown.splitlines()[2:]]
    mdvalues={row[0].strip().replace('\\|','|'):row[1].strip().replace('\\|','|') for row in mdrows if len(row)==2}
    exact('markdown_keys',k,sorted(mdvalues),sorted(flat),'export')
    for key,v in flat.items():
        got=mdvalues.get(key)
        if isinstance(v,list):
            try:mv=json.loads(got)
            except Exception:mv=None
            exact('markdown_array',k+'::'+key,mv,v,'export')
        elif isinstance(v,(int,float)):
            try:mv=float(got)
            except Exception:mv=None
            num('markdown_number',k+'::'+key,mv,v,0,category='export')
        else:exact('markdown_scalar',k+'::'+key,got,'' if v is None else str(v),'export')
    exact('report_markdown_data',k,markdown in exports.get('nma-inconsistency-report.md',''),True,'export')
    exact('report_text_data',k,all(key+': '+value in exports.get('nma-inconsistency-report.txt','') for key,value in mdvalues.items()),True,'export')
    # Coordinates derive from the exact emitted estimates, CIs and documented scale.
    valid=all(isinstance(n[p][q],(int,float)) and math.isfinite(n[p][q]) for n in ns for p in ['direct','indirect'] for q in ['mean','se'])
    exact('plot_finite_evidence',k,valid,True,'plot')
    if not valid:continue
    means=[n[p]['mean'] for n in ns for p in ['direct','indirect']]
    limits=[n[p]['mean']+sign*1.959963984540054*n[p]['se'] for n in ns for p in ['direct','indirect'] for sign in [-1,1]]
    domain=limits if variant=='patched' else means
    lo=min([0]+domain)-.3;hi=max([0]+domain)+.3
    X=lambda v:120+(v-lo)/(hi-lo)*450
    lines=[dict(re.findall(r'([\w-]+)="([^"]*)"',m)) for m in re.findall(r'<line\b([^>]*)',a['svg'])]
    exact('plot_line_count',k,len(lines),1+2*len(ns),'plot')
    exact('plot_viewbox',k,a['viewBox'],f'0 0 600 {max(200,40+len(ns)*30+20)}','plot')
    zero=lines[0] if lines else {}
    for attr,expected in [('x1',X(0)),('x2',X(0)),('y1',10),('y2',10+len(ns)*30)]:num('plot_zero_line',k+'::'+attr,float(zero[attr]) if attr in zero else None,expected,category='plot')
    rects=[dict(re.findall(r'([\w-]+)="([^"]*)"',m)) for m in re.findall(r'<rect\b([^>]*)',a['svg'])]
    exact('plot_marker_count',k,len(rects),2*len(ns)+2,'plot')
    plotlabels=[html.unescape(re.sub('<[^>]+>','',m)) for m in re.findall(r'<text\b[^>]*>(.*?)</text>',a['svg'])]
    exact('plot_labels',k,plotlabels,[n['comparison'] for n in ns]+['direct','indirect'],'plot')
    for i,n in enumerate(ns):
        for j,p in enumerate(['direct','indirect']):
            line=lines[1+2*i+j] if len(lines)>1+2*i+j else {}
            marker=rects[2*i+j] if len(rects)>2*i+j else {}
            yy=30+i*30
            for attr,expected in [('x',X(n[p]['mean'])-3.5),('y',yy-9.5 if p=='direct' else yy+2.5),('width',7),('height',7)]:num('plot_marker',k+'::'+n['comparison']+'::'+p+'::'+attr,float(marker[attr]) if attr in marker else None,expected,category='plot')
            for attr in ['y1','y2']:num('plot_CI_y',k+'::'+n['comparison']+'::'+p+'::'+attr,float(line[attr]) if attr in line else None,yy-6 if p=='direct' else yy+6,category='plot')
            for attr,sgn in [('x1',-1),('x2',1)]:
                expected=X(n[p]['mean']+sgn*1.959963984540054*n[p]['se']);got=float(line[attr]) if attr in line else None
                num('plot_CI_coordinate',k+'::'+n['comparison']+'::'+p+'::'+attr,got,expected,1e-9,category='plot')
                check('plot_CI_in_view',k+'::'+n['comparison']+'::'+p+'::'+attr,got is not None and 0<=got<=600,0 if got is not None and 0<=got<=600 else 1,got=got,expected='0..600',category='plot')
total=sum(v['checks'] for v in stats.values());passed=sum(v['passed'] for v in stats.values())
result=dict(variant=variant,checks=total,passed=passed,failed=total-passed,quantities=stats,failures=failures,reference_statuses=dict(Counter(x['status'] for x in refs)),configuration_count=len(corpus))
(OUTDIR/f'results-{variant}.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['quantity | pass/checks | max difference | tolerance']+[f"{q} | {s['passed']}/{s['checks']} | {s['max_difference']:.17g} | {s['tolerances']}" for q,s in sorted(stats.items())]+[f'{passed}/{total} checks pass']
text='\n'.join(lines)+'\n';(OUTDIR/f'comparison-{variant}.txt').write_text(text,encoding='utf-8');print(text)
