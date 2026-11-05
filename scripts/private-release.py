#!/usr/bin/env python3
"""Private repository checks and gated publication from this workflow's artifacts."""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
REPOSITORY='Celestials316/nodejs-mobile-app-lite'
def command(*args): return subprocess.check_output(args,text=True).strip()
def api(path): return json.loads(command('gh','api',path))
def load_profile():
    profile=json.loads((ROOT/'private-profile.json').read_text())
    for field in ('name','node_line','node_version','recipe_branch','android_api',
                  'ndk','abis','icu_profile','source_base','release_tag_prefix'):
        if field not in profile: raise ValueError(f'Private profile is missing {field}')
    return profile
def version():
    s=(ROOT/'mobile-src/src/node_mobile_version.h').read_text()
    values=[int(re.search(rf'^#define NODE_MOBILE_{field}\s+([0-9]+)$',s,re.M)[1])
            for field in ['MAJOR_VERSION','MINOR_VERSION','PATCH_VERSION','REVISION']]
    profile=load_profile()
    expected=tuple(int(part) for part in profile['node_version'].split('.'))
    if len(expected)!=3 or tuple(values[:3])!=expected:
        raise ValueError('This private repository only builds Node '+profile['node_version'])
    if values[0]!=int(profile['node_line']):
        raise ValueError('Private profile node_line and node_version disagree')
    return '.'.join(map(str,values[:3]))+'-'+str(values[3])
def private():
    if os.environ.get('GITHUB_REPOSITORY',REPOSITORY)!=REPOSITORY:
        raise ValueError('Publication only permitted in '+REPOSITORY)
    data=api('repos/'+REPOSITORY)
    # Identity boundary, not visibility: the repository went public on
    # 2026-10-14 to use the free standard runners (published assets are
    # world-readable; that was the reviewed tradeoff). Forks and rehosted
    # copies answer with a different full_name — and their GITHUB_REPOSITORY
    # differs — so they still cannot build or publish under this recipe.
    if data.get('full_name')!=REPOSITORY:
        raise ValueError('Refusing to build or publish outside '+REPOSITORY)
    return data
def exists(tag):
    r=subprocess.run(['gh','api',f'repos/{REPOSITORY}/git/ref/tags/{tag}'],capture_output=True,text=True)
    if r.returncode==0:return True
    if 'HTTP 404' in r.stderr:return False
    raise ValueError('Could not verify the release tag: '+r.stderr)
def output(values):
    print(json.dumps(values,indent=2))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:
            for key,value in values.items(): f.write(f'{key}={value}\n')
def preflight():
    private()
    profile=load_profile()
    v=version()
    pin=next(line.strip() for line in (ROOT/'upstream-base.txt').read_text().splitlines()
             if line.strip() and not line.lstrip().startswith('#'))
    if not re.fullmatch('[0-9a-f]{40}',pin) or pin!=profile['source_base']:
        raise ValueError('Private profile and immutable Node '+profile['node_version']+' upstream pin disagree')
    prefix=profile['release_tag_prefix']
    requested=os.environ.get('RELEASE_TAG','').strip()
    tag=requested or f'{prefix}{v}-build.{os.environ["GITHUB_RUN_ID"]}'
    if not re.fullmatch(re.escape(prefix)+re.escape(v)+r'(?:-[A-Za-z0-9][A-Za-z0-9._-]*)?',tag):
        raise ValueError('Tag must identify this private App version: '+prefix+v+'[-suffix]')
    operation=os.environ.get('BUILD_OPERATION','build')
    if operation not in ['build','build-and-release']:raise ValueError('Unknown operation')
    if operation=='build-and-release':
        expected_ref='refs/heads/'+profile['recipe_branch']
        if os.environ.get('GITHUB_EVENT_NAME')!='workflow_dispatch' or os.environ.get('GITHUB_REF')!=expected_ref:
            raise ValueError('Manual release must run on '+expected_ref)
        if exists(tag):raise ValueError('Tag already exists. Resume its original publish job; no release is overwritten.')
    output({'version':v,'tag':tag,'base':profile['source_base'],
            'branch':profile['recipe_branch'],'ndk':profile['ndk'],
            'android_api':profile['android_api']})
def publish():
    private()
    v=version();tag=os.environ['RELEASE_TAG'];sha=os.environ['GITHUB_SHA']
    folder=ROOT/'release-packages'
    subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=folder,check=True)
    source=ROOT/'source';tree=command('git','-C',str(source),'rev-parse','HEAD^{tree}')
    expected=next(l for l in (ROOT/'expected-tree.txt').read_text().splitlines() if re.fullmatch('[0-9a-f]{40}',l))
    if tree!=expected:raise ValueError('Source tree mismatch')
    note=(ROOT/'docs/PRIVATE-RELEASE-NOTES.md').read_text()
    custom=os.environ.get('RELEASE_NOTES','').strip()
    if custom: note+='\n\n'+custom+'\n'
    note+=f'\n\nRecipe: `{sha}`. Verified source tree: `{tree}`. Workflow run: https://github.com/{REPOSITORY}/actions/runs/{os.environ["GITHUB_RUN_ID"]}.\n'
    notes=Path(os.environ['RUNNER_TEMP'])/'private-publish-notes.md';notes.write_text(note)
    subprocess.run(['gh','auth','setup-git'],check=True)
    # Snapshot commits preserve the complete source without upstream history import.
    if exists(tag):
        subprocess.run(['git','-C',str(source),'fetch',f'https://github.com/{REPOSITORY}.git',f'refs/tags/{tag}:refs/tags/{tag}'],check=True)
        if command('git','-C',str(source),'rev-parse',tag+'^{tree}')!=tree or f'Recipe-Commit: {sha}' not in command('git','-C',str(source),'cat-file','tag',tag):
            raise ValueError('Existing tag belongs to a different build')
    else:
        message=f'Private Android App lite {v}\n\nRecipe-Commit: {sha}\nSource-Tree: {tree}\n'
        commit=subprocess.check_output(['git','-C',str(source),'commit-tree',tree],input=message,text=True).strip()
        subprocess.run(['git','-C',str(source),'tag','-a',tag,commit,'-m',message],check=True)
        subprocess.run(['git','-C',str(source),'push',f'https://github.com/{REPOSITORY}.git',f'refs/tags/{tag}'],check=True)
    r=subprocess.run(['gh','release','view',tag,'--repo',REPOSITORY,'--json','isDraft'],capture_output=True,text=True)
    if r.returncode==0:
        if not json.loads(r.stdout)['isDraft']: raise ValueError('Published releases cannot be overwritten')
    else:
        subprocess.run(['gh','release','create',tag,'--repo',REPOSITORY,'--draft','--prerelease','--latest=false',
                        '--title',f'Private Android App lite {v} + HTTP/3','--notes-file',str(notes),'--verify-tag'],check=True)
    private()
    subprocess.run(['gh','release','upload',tag,'--repo',REPOSITORY,'--clobber',*[str(p) for p in sorted(folder.iterdir()) if p.is_file()]],check=True)
    private()
    subprocess.run(['gh','release','edit',tag,'--repo',REPOSITORY,'--draft=false','--prerelease','--latest=false'],check=True)
    print(f'https://github.com/{REPOSITORY}/releases/tag/{tag}')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('operation',choices=['version','preflight','publish']);args=ap.parse_args()
    if args.operation=='version': print(version())
    elif args.operation=='preflight': preflight()
    else:publish()
if __name__=='__main__':
    try:main()
    except (ValueError,subprocess.CalledProcessError) as error:print('::error::'+str(error),file=sys.stderr);sys.exit(1)
