import pathlib, shutil, re, hashlib, json, subprocess, os
root=pathlib.Path(__file__).resolve().parent
source=pathlib.Path(os.environ.get('ALLMETA_ROOT',str(root.parent/'allmeta')))
out=root/'app-original'
paths={'nma-inconsistency/index.html','nma-inconsistency/README.md','LICENSE'}
html=(source/'nma-inconsistency/index.html').read_text(encoding='utf-8')
for p in re.findall(r'(?:src|href)="(\.\./[^"?#]+\.(?:js|css))"',html):
    paths.add(str(pathlib.PurePosixPath(p[3:])))
for p in list(paths):
    if not (source/p).is_file(): continue
    (out/p).parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source/p,out/p)
manifest={p:hashlib.sha256((out/p).read_bytes()).hexdigest() for p in sorted(paths) if (out/p).is_file()}
(root/'source-manifest.json').write_text(json.dumps({'commit':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),'files':manifest},indent=2)+'\n')
(root/'documentation').mkdir(exist_ok=True)
for p in (source/'hub/shared/tests').glob('nma-inconsistency*-parity.spec.mjs'):
    shutil.copyfile(p,root/'documentation'/p.name)
print('Copied',len(manifest),'source files')
