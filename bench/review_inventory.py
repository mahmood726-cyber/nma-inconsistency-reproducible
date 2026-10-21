import json,csv,re
from pathlib import Path
items=json.loads(Path('dataset-ledger.json').read_text(encoding='utf-8'))
reasons={
'dat.bauer2002':'one treatment contrast (OM-89 versus control); no third treatment identity',
'dat.begg1989':'two treatment types (bone-marrow transplantation and chemotherapy); arm-level example, not a multi-treatment network',
'dat.besson2016':'heterogeneous animal manipulations, outcomes, repeated animals and shared controls; no documented treatment-node network or unique independent trial reconstruction; not relabeled as an NMA',
'dat.cohen1981':'correlations; control is a study-design moderator, not a comparator-treatment identity',
'dat.curtis1998':'elevated versus ambient CO2; xtrt/level are experimental moderators, not a documented multi-treatment trial network',
'dat.huber2000':'individual-patient data for Uro-Vaxom versus placebo only; two treatments',
'dat.knapp2017':'schizophrenia versus healthy controls; task/difficulty and overlapping group IDs describe dependent outcomes, not alternative treatments',
'dat.landenberger2005':'CBT versus control; intervention-component indicators do not identify alternative study arms for an NMA',
'dat.lehmann2018':'red-versus-control experiments with mixed designs and repeated samples; Color_Control can suggest a color network but no documented network/study covariance construction is supplied; excluded as a non-network collection, not claimed numerically validated',
'dat.mccurdy2020':'generation versus reading experiments; multiple conditions/outcomes and dependent samples, not a documented treatment network',
'dat.metap':'collections of p-values; no treatment contrasts and sampling variances',
'dat.michael2013':'brain image versus no brain image only; two conditions',
'dat.molloy2014':'correlations; controls is a covariate-adjustment variable, not a comparator arm',
'dat.roever2022':'single-arm dose-toxicity data without within-study randomized treatment comparisons',
'dat.spooner2002':'nedocromil versus placebo only; agegroup is a moderator, not a treatment arm',
'dat.thompson1999':'cholesterol-lowering intervention versus control only; cholr is a continuous moderator',
'dat.ursino2021':'single-arm dose-toxicity data without within-study randomized treatment comparisons',
'dat.viechtbauer2021':'hypothetical treatment-versus-control model-checking examples; dose is a continuous moderator, not a documented multi-treatment network',
'dat.white2020':'correlations between signals and quality; control/exp_obs are study-design moderators, not treatment alternatives',
}
for x in items:
    x['decision']='included' if x['configurations'] else 'excluded'
    if x['dataset'] in reasons and not x['configurations']:x['reason']='excluded: '+reasons[x['dataset']]
    if not x['configurations'] and x['dataset'] not in reasons:
        x['reason']='excluded: '+x['title']+'; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes'
    x['documentation']='documentation/'+x['package']+'-'+x['dataset']+'.txt'
Path('dataset-ledger.json').write_text(json.dumps(items,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with Path('dataset-ledger.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['package','dataset','decision','configurations','reason','documentation']);w.writeheader();w.writerows({k:x[k] for k in w.fieldnames} for x in items)
print(len(items),'dataset decisions recorded; all treatment-like candidate exclusions manually reviewed')
