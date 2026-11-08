"""Recompute fixed comparisons, controls, and the complete Tanakh corpus."""
from pathlib import Path
import argparse,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
steps=[
 ('comparisons',[sys.executable,'run/reproduce_comparisons.py']),
 ('poetic_comparators',[sys.executable,'src/analysis/poetic_comparators.py']),
 ('extension_summary',[sys.executable,'src/analysis/comparator_summary.py']),
 ('extension_validation',[sys.executable,'src/analysis/validate_controls.py']),
 ('tanakh',[sys.executable,'run/tanakh.py','all']),
 ('integration',[sys.executable,'src/analysis/validate_integration.py']),
 ('tanakh_word_control_validation',[sys.executable,'run/tanakh_word_control.py','--verify']),
]
completed=[]
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--offline',action='store_true',help='Disallow external source fetching; Rivlin must be supplied locally')
    args=ap.parse_args()
    if args.offline:
        # Fail before expensive calculations, not at the late additional-sources stage.
        subprocess.run([sys.executable,'src/additional_sources.py','--check','--offline'],cwd=ROOT,check=True)
    target=ROOT/'.local/validation/reproduction_all.json';target.parent.mkdir(parents=True,exist_ok=True)
    try:
        for name,command in steps:
            print('Stage:',name,flush=True)
            subprocess.run(command,cwd=ROOT,check=True,env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',**({'HASHIRA_OFFLINE':'1'} if args.offline else {})))
            completed.append(name)
    finally:
        target.write_text(json.dumps({'status':'PASS' if len(completed)==len(steps) else 'INCOMPLETE','completed_stages':completed},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
