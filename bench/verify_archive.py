import json,hashlib,subprocess,shutil,tempfile,re,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent
read=lambda p:json.loads((root/p).read_text(encoding='utf-8'))
corpus=read('corpus.json');refs=read('reference.json');original=read('app-original.json');patched=read('app-patched.json')
keys=[x['key'] for x in corpus]
assert len(keys)==len(set(keys))
for name,rows in [('reference',refs),('original',original),('patched',patched)]:
    ks=[x['key'] for x in rows];assert len(ks)==len(set(ks)) and set(ks)==set(keys),name
assert not [r for r in refs if r['status']=='error']
for r in refs:
    if r['key'].endswith('::PM') and r['status']=='ok':assert r.get('pm_reference')=='uncentered package QE'
result=read('results-patched.json');focused=read('focused-patched.json')
assert result['passed']==result['checks'] and focused['passed']==focused['checks']
manifest=read('source-manifest.json')
for rel,digest in manifest['files'].items():
    assert hashlib.sha256((root/'app-original'/rel).read_bytes()).hexdigest()==digest
    upstream=root.parent/'allmeta'/rel
    if upstream.exists():assert hashlib.sha256(upstream.read_bytes()).hexdigest()==digest
test=root/f'patch-replay-check-{len(list(root.glob("patch-replay*")))+1}'
test.mkdir()
shutil.copytree(root/'app-original',test,dirs_exist_ok=True)
subprocess.run(['git','-C',str(test),'apply','--check',str(root/'fix.patch')],check=True,capture_output=True)
subprocess.run(['git','-C',str(test),'apply',str(root/'fix.patch')],check=True,capture_output=True)
for rel in ['nma-inconsistency/index.html','nma-inconsistency/README.md']:
    assert (test/rel).read_text(encoding='utf-8')==(root/'app-patched'/rel).read_text(encoding='utf-8')
# No deletion is required: the small replay directory stays outside the archive.
excluded={'TASK.md','RUN.json','codex.log','debug_corpus.R','debug_corpus.log','probe.R','probe.log','P16-validation.zip','archive-manifest.json'}
allowed={'.R','.py','.cjs','.json','.csv','.md','.txt','.log','.patch'}
files=[p for p in root.iterdir() if p.is_file() and p.name not in excluded and p.suffix in allowed]
for folder in ['documentation','reference','app-original','app-patched']:
    files += [p for p in (root/folder).rglob('*') if p.is_file()]
pattern=re.compile(r'[A-Za-z]:[/\\](?:Users|Projects|claude)[/\\]')
for p in files:
    text=p.read_text(encoding='utf-8',errors='replace')
    assert not pattern.search(text),'machine path in '+str(p.relative_to(root))
verification={'configuration_keys':len(keys),'unique_exact_coverage':True,'reference_errors':0,'patched_checks':result['checks'],'patched_passed':result['passed'],'focused_checks':focused['checks'],'focused_passed':focused['passed'],'patch_replay_matches':True,'source_files_unchanged':True,'portable_path_scan':True,'browser_evidence':False}
(root/'verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
summary=read('results.json')
(root/'PROGRESS.md').write_text(f'''# P16 completed

Source commit: {manifest['commit']}. Upstream source files are unchanged; no
commit or push was made. The proposed app-only fix.patch was replayed and matches
the patched source snapshot.

127 datasets enumerated; 36 included; {len(keys)} unique configurations.
Original: {summary['original']['passed']}/{summary['original']['checks']} checks pass.
Patched: {result['passed']}/{result['checks']} checks pass.
Focused: {focused['passed']}/{focused['checks']} patched checks pass.
Reference status counts: {summary['reference_statuses']}.

All required artifacts and reproduction commands are indexed in RESULTS.md and
README.md. verification.json records exact coverage, source hashes, patch replay,
and the portable-path scan. P16-validation.zip packages the audit and evidence.

Limits: execution used the explicitly permitted Node route after Edge failed to
launch. Generated markup and serializers were checked; live browser layout was
not validated. Multi-arm inputs are safety-refused, not numerically validated;
three native-study-versus-flattened R diagnostics quantify that limitation.
''',encoding='utf-8')
files=[p for p in files if p.name!='verification.json']+[root/'verification.json']
inventory={str(p.relative_to(root)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)}
(root/'archive-manifest.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(root/'P16-validation.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(files+[root/'archive-manifest.json']):z.write(p,'P16-validation/'+p.relative_to(root).as_posix())
print(f'{len(keys)} unique configurations verified; patch replay matches; source unchanged; archive contains {len(files)+1} files')
