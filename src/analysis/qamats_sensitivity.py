"""Targeted sensitivity: recode lexical כָּל from frozen Biblical U+05B8 a to reader-facing o.
This does not alter the frozen article analysis; it quantifies the known qamats-qatan source asymmetry.
"""
import csv,json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(P/'src/core'),str(P/'src/preparation'),str(P/'src/analysis')]
from phonetic_core_v2 import transliterate_word
from prepare_biblical_reading import adapt
from compare_modes import compute_coverage
TOKEN=re.compile(r'[א-ת][א-ת\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]*')

def main():
    base={}
    with (P/'results/comparison/coverage.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            if r['block']=='512' and r['offset']=='0' and r['radius']=='64':base[(r['corpus'],r['mode'])]=float(r['mean'])
    rows=[]
    for book in ['genesis','exodus','leviticus','numbers','deuteronomy']:
        vs=json.loads((P/f'sources/original/biblical/{book}_verses.json').read_text(encoding='utf-8'))['verses'];seq=[];changed=0
        for v in vs:
            text,_,_=adapt(v['source_text'])
            for m in TOKEN.finditer(text):
                tok=m.group();u=transliterate_word(tok,return_units=True);letters=''.join(c for c in tok if '\u05d0'<=c<='\u05ea')
                if letters=='כל' and '\u05b8' in tok and u==['k','a','l']:
                    u=['k','o','l'];changed+=1
                seq+=u
        trial,_=compute_coverage(book.title(),[seq])
        for mode in ('exact','expanded'):
            value=next(r for r in trial if r['mode']==mode and r['block']==512 and r['offset']==0 and r['radius']==64)['mean'];baseline=base[(book.title(),mode)]
            rows.append(dict(corpus=book.title(),mode=mode,lexical_kol_tokens_recoded=changed,baseline=baseline,recoded=value,difference_percentage_points=(value-baseline)*100))
    out=P/'results/qamats_kol_sensitivity.csv'
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    print('PASS qamats sensitivity; max absolute change (percentage points):',max(abs(r['difference_percentage_points']) for r in rows))
if __name__=='__main__':main()
