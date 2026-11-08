"""Deterministic illustration: first eligible Genesis block, first local permutation."""
import json,random
from spatial import P,corpus_words,fragment,score
words=corpus_words()['Genesis'][0][:128]
frags=[fragment(words[i:i+8]) for i in range(0,128,8)]
order=list(range(16)); shuffled=order.copy();random.Random(2026102601).shuffle(shuffled)
rows=[]
for i in order:
 rows.append({'fragment':i+1,'reading':' '.join(''.join(w) for w in words[i*8:i*8+8])})
a,n=score(frags,order);b,m=score(frags,shuffled)
assert n==m
out={'selection':'First eligible Genesis block; first specified local permutation; no score-based selection','radius':64,'observed_covered':a,'shuffled_covered':b,'units':n,'observed':a/n,'shuffled':b/n,'order':[i+1 for i in order],'shuffled_order':[i+1 for i in shuffled],'fragments':rows}
(P/'results/worked_example.json').write_text(json.dumps(out,indent=2),encoding='utf-8',newline='\n')
print(f"PASS worked example: observed={a/n:.4%}; rearranged={b/m:.4%}")
