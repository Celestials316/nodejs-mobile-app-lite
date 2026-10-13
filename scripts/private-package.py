#!/usr/bin/env python3
"""Package only the private Android SDK, with strict payload/provenance checks."""
import argparse,datetime,hashlib,json,os
from pathlib import Path
import re,subprocess,zipfile
ROOT=Path(__file__).resolve().parent.parent
ABIS=('arm64-v8a','armeabi-v7a','x86_64')
def run(*args): return subprocess.check_output(args,text=True)
def validate_elf(path,readelf):
    headers=run(readelf,'-lW',str(path))
    loads=[line.split() for line in headers.splitlines() if line.strip().startswith('LOAD ')]
    if not loads or any(int(parts[-1],16)<16384 for parts in loads):
        raise ValueError(f'{path}: LOAD segments do not support 16 KB pages')
    dynamic=run(readelf,'-d',str(path))
    if 'BIND_NOW' not in dynamic or 'GNU_RELRO' not in headers:
        raise ValueError(f'{path}: RELRO/NOW must remain enabled')
    if not re.search(r'ANDROID_REL(?:A)?\)',dynamic):
        raise ValueError(f'{path}: missing API23-compatible APS2 relocation packing')
    if 'RELR' in dynamic:
        raise ValueError(f'{path}: RELR would raise the API floor above 24')
    needed=re.findall(r'Shared library: \[([^]]+)\]',dynamic)
    if set(needed)-{'libc.so','libdl.so','libm.so','liblog.so','libc++_shared.so'}:
        raise ValueError(f'{path}: unexpected external dependencies {needed}')
    print(f'{path}: ELF, 16 KB pages, APS2 and RELRO/NOW OK')
def package(source,out):
    version=run('python3',str(ROOT/'scripts/private-release.py'),'version').strip()
    for abi in ABIS:
        if not (source/'bin'/abi/'libnode.so').is_file(): raise ValueError(f'Missing {abi}')
    if not (source/'include/node/node.h').is_file(): raise ValueError('Missing JNI/Node headers')
    source_tree=(ROOT/'expected-tree.txt').read_text().splitlines()[-1]
    info={'profile':'danmu-android-lite-h3','node':'24.22.0','mobile':version,
          'upstream':next(l.strip() for l in (ROOT/'upstream-base.txt').read_text().splitlines() if l.strip() and not l.startswith('#')),
          'source_tree':source_tree,'recipe':os.environ.get('GITHUB_SHA',run('git','-C',str(ROOT),'rev-parse','HEAD').strip()),
          'run':os.environ.get('GITHUB_RUN_ID'),'repository':os.environ.get('GITHUB_REPOSITORY','Celestials316/nodejs-mobile-app-lite'),
          'platform':'android','abis':ABIS,'android_api':24,'ndk':'r27d','quic':True,
          'icu_profile':'danmu-lite','files':{}}
    for abi in ABIS:
        p=source/'bin'/abi/'libnode.so';info['files'][f'bin/{abi}/libnode.so']={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    (source/'BUILD-INFO.json').write_text(json.dumps(info,indent=2)+'\n')
    if not (source/'LICENSE').is_file(): raise ValueError('Missing materialized-source license')
    files=sorted(p for p in source.rglob('*') if p.is_file())
    for p in files:
        relative=p.relative_to(source)
        if relative.parts[0] not in {'bin','include','BUILD-INFO.json','LICENSE'} or p.is_symlink():
            raise ValueError(f'Unexpected payload {relative}')
    out.mkdir(parents=True,exist_ok=True)
    target=out/f'nodejs-mobile-android-app-lite-{version}.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files: z.write(p,p.relative_to(source))
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None: raise ValueError('Archive integrity failed')
    (out/'SHA256SUMS').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    print(json.dumps(info,indent=2))
def main():
    ap=argparse.ArgumentParser();subs=ap.add_subparsers(dest='command',required=True)
    check=subs.add_parser('validate-elf');check.add_argument('path',type=Path);check.add_argument('--readelf',default='llvm-readelf')
    pack=subs.add_parser('package');pack.add_argument('source',type=Path);pack.add_argument('out',type=Path)
    args=ap.parse_args()
    if args.command=='validate-elf': validate_elf(args.path,args.readelf)
    else: package(args.source,args.out)
if __name__=='__main__': main()
