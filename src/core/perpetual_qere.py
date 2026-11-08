"""Explicit lexical qere perpetuum; Gesenius–Kautzsch–Cowley §17c.
Used only for internal pronunciation input. Original source remains unchanged.
"""
import re
GRAPHEME=re.compile(r'[א-ת][\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7]*')
PREFIX=set('ובכלמשה')
def normalize(token):
    g=GRAPHEME.findall(token);b=''.join(x[0] for x in g);rules=[]
    def suffix(s):return b.endswith(s) and all(x in PREFIX for x in b[:-len(s)])
    if suffix('הוא') and '\u05b4' in g[-3] and len(g[-2])==1 and len(g[-1])==1:
        g[-2]='י';rules.append('qere_hi')
    elif suffix('ירושלם') and '\u05b4' in g[-2] and any(c in g[-2] for c in '\u05b7\u05b8'):
        g[-2]=g[-2].replace('\u05b4','');g.insert(len(g)-1,'יִ');rules.append('qere_yerushalayim')
    elif suffix('יששכר') and '\u05c2' in g[-4] and len(g[-3])==1:
        del g[-3];rules.append('qere_yissakhar')
    return (''.join(g) if rules else token),rules
