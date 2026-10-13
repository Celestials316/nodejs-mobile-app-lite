#!/usr/bin/env python3
"""Private App configuration and workflow guard regressions."""
from pathlib import Path
import importlib.util,json,os,shlex,subprocess,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent.parent
SOURCE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'out'
if len(sys.argv)>1: del sys.argv[1]
CUTS={'--without-amaro','--without-inspector','--without-sqlite',
      '--disable-single-executable-application','--v8-disable-object-print',
      '--without-npm','--without-corepack'}
class PrivateProfile(unittest.TestCase):
    def configure(self,folder,arch,flavor='lite',code=0):
        ndk=folder/'ndk';ndk.mkdir(exist_ok=True);(ndk/'marker').touch()
        capture=folder/'capture.json'
        program=folder/'configure'
        program.write_text(f'#!{sys.executable}\nimport json,sys,os\n'
            f'open({str(capture)!r},"w").write(json.dumps({{"flags":sys.argv[1:],"gyp":os.environ["GYP_DEFINES"]}}))\nsys.exit({code})\n')
        program.chmod(0o755)
        command=[sys.executable,'-c',
            "import platform,runpy,sys;platform.system=lambda:'Linux';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')",
            str(SOURCE/'android_configure.py'),str(ndk),'24',arch]
        env=dict(os.environ,NODEJS_MOBILE_FLAVOR=flavor);env.pop('NODEJS_MOBILE_SCCACHE',None)
        result=subprocess.run(command,cwd=folder,env=env,capture_output=True,text=True)
        return result,json.loads(capture.read_text()) if capture.exists() else None
    def test_all_app_abis_keep_network_icu_and_engine(self):
        for arch in ['arm','arm64','x86_64']:
            with self.subTest(arch=arch),tempfile.TemporaryDirectory() as d:
                result,config=self.configure(Path(d),arch)
                self.assertEqual(result.returncode,0,result.stderr)
                flags=set(config['flags'])
                self.assertTrue(CUTS <= flags)
                self.assertTrue({'--experimental-quic','--with-intl=full-icu','--shared','--cross-compiling'} <= flags)
                self.assertIn('node_mobile_icu_profile=danmu-lite.json',config['gyp'])
                self.assertEqual('--experimental-enable-pointer-compression' in flags,arch!='arm')
                self.assertFalse(flags & {'--without-ssl','--without-node-options','--v8-lite-mode','--without-v8-platform','--without-siphash'})
    def test_full_build_and_configure_failures_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            result,_=self.configure(Path(d),'arm64',flavor='full')
            self.assertNotEqual(result.returncode,0)
        with tempfile.TemporaryDirectory() as d:
            result,_=self.configure(Path(d),'arm64',code=7)
            self.assertEqual(result.returncode,7)
    def test_quic_default_native_wasm_and_public_icu_profile(self):
        self.assertIn('bool experimental_quic = true;', (SOURCE/'src/node_options.h').read_text())
        self.assertNotIn("'deps/polywasm/polywasm.js'",(SOURCE/'node.gyp').read_text())
        self.assertNotIn("require('internal/deps/polywasm/polywasm')",(SOURCE/'lib/internal/process/pre_execution.js').read_text())
        self.assertIn('en',json.loads((SOURCE/'tools/icu/danmu-lite.json').read_text())['variables']['locales']['only'])
    def test_workflow_only_private_android_lite_and_gated_publication(self):
        import yaml
        names=sorted(p.name for p in (ROOT/'.github/workflows').glob('*.yml'))
        self.assertEqual(names,['android-lite.yml'])
        workflow=yaml.load((ROOT/'.github/workflows/android-lite.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(workflow['env']['NODEJS_MOBILE_FLAVOR'],'lite')
        self.assertNotIn('schedule',workflow['on'])
        self.assertEqual(workflow['jobs']['build']['strategy']['matrix']['arch'],['arm','arm64','x86_64'])
        self.assertEqual(workflow['jobs']['package']['needs'],['prepare','build','test'])
        self.assertEqual(workflow['jobs']['release']['needs'],['prepare','package'])
        self.assertIn("operation == 'build-and-release'",workflow['jobs']['release']['if'])
        self.assertIn('--latest=false',(ROOT/'scripts/private-release.py').read_text())
        self.assertIn('isDraft',(ROOT/'scripts/private-release.py').read_text())
        for job in workflow['jobs'].values():
            self.assertEqual(job['runs-on'],'ubuntu-24.04')
        prepare=str(workflow['jobs']['prepare'])
        self.assertIn('private',prepare);self.assertIn('Celestials316/nodejs-mobile-app-lite',(ROOT/'scripts/private-release.py').read_text())
    def test_icu_resources_and_strip_contract(self):
        spec=importlib.util.spec_from_file_location('flavors',ROOT/'scripts/test-mobile-flavors.py')
        module=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(spec.origin),str(SOURCE)]):
            spec.loader.exec_module(module)
        case=module.MobileFlavors('test_icu_profile_required_resources_exist_in_pinned_data')
        result=unittest.TestResult();case.run(result)
        self.assertTrue(result.wasSuccessful(),result.errors+result.failures)
if __name__=='__main__': unittest.main()
