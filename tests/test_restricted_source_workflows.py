"""Release interfaces must keep restricted source access explicit."""
import hashlib, json, os, subprocess, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from additional_sources import ActualTextParser, verify_rivlin_html, available_rivlin_path

class RestrictedWorkflowTests(unittest.TestCase):
    def test_exact_extracted_text_and_wrong_hash_rejected(self):
        html=b'<div id="actualtext"><p>hello</p></div>'
        expected='hello\n'
        self.assertEqual(verify_rivlin_html(html,hashlib.sha256(expected.encode()).hexdigest()),expected)
        with self.assertRaises(ValueError):verify_rivlin_html(html,'0'*64)
    def test_unavailable_source_does_not_download_during_check(self):
        path=R/'.local'/'not_a_real_rivlin_source.html'
        env=dict(os.environ,HASHIRA_RIVLIN_HTML=str(path),HASHIRA_OFFLINE='1')
        result=subprocess.run([sys.executable,str(R/'src/additional_sources.py'),'--check','--offline'],cwd=R,env=env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('HASHIRA_RIVLIN_HTML',result.stderr)
    def test_runner_is_explicit_about_offline_scope(self):
        a=(R/'run/reproduce_offline.py').read_text(encoding='utf-8')
        self.assertNotIn('reproduce_all.py',a)
        self.assertIn('tanakh.py',a)
        b=(R/'run/reproduce_all.py').read_text(encoding='utf-8')
        self.assertIn('--offline',b)

if __name__=='__main__':unittest.main()
