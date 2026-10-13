#!/usr/bin/env python3
"""Ensure repository visibility and duplicate/tag checks fail closed."""
import importlib.util,os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('private_release',Path(__file__).with_name('private-release.py'))
CONTROL=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(CONTROL)
class PrivateRelease(unittest.TestCase):
    def env(self,**extra):
        return patch.dict(os.environ,{'GITHUB_REPOSITORY':'Celestials316/nodejs-mobile-app-lite',
          'GITHUB_RUN_ID':'42','GITHUB_REF':'refs/heads/recipe',
          'GITHUB_EVENT_NAME':'workflow_dispatch','BUILD_OPERATION':'build-and-release','RELEASE_TAG':'',**extra})
    def test_public_repository_and_other_owner_are_rejected(self):
        with self.env(),patch.object(CONTROL,'api',return_value={'private':False,'visibility':'public'}):
            with self.assertRaises(ValueError):CONTROL.private()
        for repository in ['fogtape/nodejs-mobile','lilixu3/nodejs-mobile']:
            with self.env(GITHUB_REPOSITORY=repository):
                with self.assertRaises(ValueError):CONTROL.private()
    def test_only_404_means_absent(self):
        for code in [403,429,500]:
            r=subprocess.CompletedProcess([],1,'',f'HTTP {code}')
            with patch.object(CONTROL.subprocess,'run',return_value=r),self.assertRaises(ValueError):CONTROL.exists('tag')
        with patch.object(CONTROL.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','HTTP 404')):
            self.assertFalse(CONTROL.exists('tag'))
    def test_manual_release_branch_and_tag_reservation(self):
        with self.env(),patch.object(CONTROL,'private'),patch.object(CONTROL,'exists',return_value=False),patch.object(CONTROL,'output') as output:
            CONTROL.preflight();self.assertEqual(output.call_args[0][0]['tag'],'app-lite-v24.22.0-1-build.42')
        for options in [{'GITHUB_EVENT_NAME':'push'},{'GITHUB_REF':'refs/heads/dev'},
                        {'RELEASE_TAG':'v24.22.0-0'},{'RELEASE_TAG':'app-lite-v26.11.0-0'},
                        {'RELEASE_TAG':'app-lite-v24.22.0-1; bad'}]:
            with self.env(**options),patch.object(CONTROL,'private'),patch.object(CONTROL,'exists',return_value=False),self.assertRaises(ValueError):CONTROL.preflight()
        with self.env(),patch.object(CONTROL,'private'),patch.object(CONTROL,'exists',return_value=True),self.assertRaises(ValueError):CONTROL.preflight()
    def test_source_package_rejects_missing_abi_and_unknown_files(self):
        spec=importlib.util.spec_from_file_location('private_package',Path(__file__).with_name('private-package.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sdk';source.mkdir()
            with self.assertRaises(ValueError):mod.package(source,root/'out')
            for abi in mod.ABIS:
                lib=source/'bin'/abi/'libnode.so';lib.parent.mkdir(parents=True);lib.write_bytes(b'fixture')
            h=source/'include/node/node.h';h.parent.mkdir(parents=True);h.write_text('fixture')
            (source/'LICENSE').write_text('source-license')
            (source/'secret.txt').write_text('must not be packaged')
            with self.assertRaisesRegex(ValueError,'Unexpected payload'):mod.package(source,root/'out')
    def test_elf_api_floor_and_hardening_are_enforced(self):
        spec=importlib.util.spec_from_file_location('private_package',Path(__file__).with_name('private-package.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        headers='LOAD 0 0 0 0 0 R E 0x4000\nGNU_RELRO\n'
        dynamic='BIND_NOW (ANDROID_RELA)\nShared library: [libc.so]\n'
        with patch.object(mod,'run',side_effect=[headers,dynamic]):mod.validate_elf(Path('fixture'),'readelf')
        for h,d in [(headers.replace('0x4000','0x1000'),dynamic),(headers,dynamic+'RELR'),
                    (headers,dynamic.replace('BIND_NOW','')), (headers,dynamic+'Shared library: [libunknown.so]')]:
            with patch.object(mod,'run',side_effect=[h,d]),self.assertRaises(ValueError):mod.validate_elf(Path('fixture'),'readelf')
if __name__=='__main__':unittest.main()
