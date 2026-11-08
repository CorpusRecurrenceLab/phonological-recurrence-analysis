#!/usr/bin/env python3
from __future__ import annotations
import argparse, bisect, csv, hashlib, importlib.util, json, math, random, statistics, sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'src'
CORE=SRC/'core'
sys.path.insert(0,str(SRC/'preparation'))
sys.path.insert(0,str(SRC))
sys.path.insert(0,str(CORE))
sys.path.insert(0, str(ROOT))
from src.tanakh import prepare as s2  # explicit Tanakh module; src/prepare.py is unrelated
from phonetic_core_v2 import transliterate_word
from prepare_biblical_reading import adapt

V=set('aeiou'); RADII=(32,64,128)
PAIRS=(('f','v'),('p','b'),('d','t'),('b','v'),('z','s'),('h','kh'),('q','k'))
NEAR=defaultdict(set)
for a,b in PAIRS: NEAR[a].add(b); NEAR[b].add(a)

@lru_cache(None)
def variants(t):
    return tuple(sorted({t[:i]+(b,)+t[i+1:] for i,a in enumerate(t) for b in NEAR[a]}))

def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))

def close(a,b,tol=2e-11):
    if a is None or b is None: return a is None and b is None
    return abs(float(a)-float(b)) <= tol

def prepare_stream(book_row, raw_dir, configs):
    book=book_row['source_book']
    path=raw_dir/f"{int(book_row['order']):02d}_{s2.safe_slug(book)}.json"
    if not path.is_file(): raise FileNotFoundError(f'Missing frozen source cache: {path}')
    data=path.read_bytes()
    got=s2.git_blob_sha1(data)
    if got!=book_row['git_blob_sha1']:
        raise ValueError(f'Git blob mismatch for {book}: expected {book_row["git_blob_sha1"]}, got {got}')
    obj=json.loads(data.decode('utf-8')); text=obj['text']
    sounds=[]; words=[]; psalm_boundaries=[]
    for ci,chapter in enumerate(text,1):
        if book=='Psalms' and ci>1: psalm_boundaries.append(len(sounds))
        for vi,source in enumerate(chapter,1):
            ref=f'{book} {ci}:{vi}'
            source,_=s2.strip_editorial_tail(source,ref,configs['editorial'])
            reading,_edits,_=adapt(source)
            reading,_=s2.omit_ketiv_without_qere(reading,ref,configs['kwq'])
            for m in s2.TOKEN.finditer(reading):
                units=transliterate_word(m.group(),return_units=True)
                if not units: raise ValueError(f'Unresolved primary token at {ref}: {m.group()}')
                words.append((units,ci)); sounds.extend(units)
    invalid=set()
    for b in psalm_boundaries: invalid.update((b-2,b-1))
    return sounds,words,invalid

def occurrences(s,invalid=None,base=0):
    out=[]
    for i in range(len(s)-2):
        if invalid is not None and base+i in invalid: continue
        t=tuple(s[i:i+3]); nv=sum(x in V for x in t)
        if 0<nv<3: out.append((t,i))
    return out

def nearest(ps,i):
    k=bisect.bisect_right(ps,i-3); best=i-ps[k-1] if k else 10**9
    k=bisect.bisect_left(ps,i+3)
    return min(best,ps[k]-i if k<len(ps) else 10**9)

def coverage_counts(length,items):
    occ=defaultdict(list)
    for t,i in items: occ[t].append(i)
    marks=[[bytearray(length) for _ in RADII] for _ in range(2)]
    for t,positions in occ.items():
        others=[occ[v] for v in variants(t) if v in occ]
        for i in positions:
            exact=nearest(positions,i); expanded=exact
            for ps in others: expanded=min(expanded,nearest(ps,i))
            for mode,d in enumerate((exact,expanded)):
                for k,r in enumerate(RADII):
                    if d<=r: marks[mode][k][i:i+3]=b'\1\1\1'
    return [[sum(m) for m in row] for row in marks]

def similarity(a,b):
    den=len(a)+len(b)
    if not den:return 0.0,0.0
    adj={x:sorted(({x}|set(variants(x)))&b) for x in sorted(a)}; matched={}
    def augment(x,seen):
        for y in adj[x]:
            if y in seen: continue
            seen.add(y)
            if y not in matched or augment(matched[y],seen): matched[y]=x; return True
        return False
    for x in adj: augment(x,set())
    return 2*len(a&b)/den, 2*len(matched)/den

def coverage_grid(s,invalid):
    total=len(s); out=[]
    for L in (512,1280):
        for offset in (0,L//2):
            vals={(m,r):[] for m in ('exact','expanded') for r in RADII}
            for start in range(offset,len(s)-L+1,L):
                c=coverage_counts(L,occurrences(s[start:start+L],invalid,start))
                for mi,m in enumerate(('exact','expanded')):
                    for ri,r in enumerate(RADII): vals[m,r].append(c[mi][ri]/L)
            for m in ('exact','expanded'):
                for r in RADII:
                    v=vals[m,r]
                    out.append({'mode':m,'block':L,'offset':offset,'radius':r,'blocks':len(v),
                                'retained_fraction':len(v)*L/total if v else None,
                                'mean':statistics.mean(v) if v else None})
    return out

def distance_grid(s,invalid):
    total=len(s); out=[]
    for cap,L in ((256,512),(1024,1280),(4096,4352)):
        gaps=[g for g in (0,64,256,1024,4096) if g<=cap]
        for offset in (0,L//2):
            for phase in (0,64):
                blocks={(m,g):[] for m in ('exact','expanded') for g in gaps}; anchors=0
                for start in range(offset,len(s)-L+1,L):
                    cache={}
                    def motifs(i):
                        if i not in cache: cache[i]={t for t,_ in occurrences(s[i:i+64],invalid,i)}
                        return cache[i]
                    vals={(m,g):[] for m in ('exact','expanded') for g in gaps}
                    for i in range(start+phase,start+L-128-cap+1,128):
                        anchors+=1
                        for gap in gaps:
                            sc=similarity(motifs(i),motifs(i+64+gap))
                            for mi,m in enumerate(('exact','expanded')): vals[m,gap].append(sc[mi])
                    for key,v in vals.items():
                        if v: blocks[key].append(statistics.mean(v))
                nb=max((len(v) for v in blocks.values()),default=0)
                for m in ('exact','expanded'):
                    for gap in gaps:
                        v=blocks[m,gap]
                        out.append({'mode':m,'cap':cap,'block':L,'offset':offset,'phase':phase,'gap':gap,
                                    'blocks':len(v),'anchors':anchors,'retained_fraction':len(v)*L/total if v else None,
                                    'mean':statistics.mean(v) if v else None})
    return out

def fragment(ws,psalm_sensitive=False):
    seq=[]; invalid=set(); pos=0; prev=None
    for units,ch in ws:
        if psalm_sensitive and prev is not None and ch!=prev: invalid.update((pos-2,pos-1))
        seq.extend(units); pos+=len(units); prev=ch
    return len(seq),occurrences(seq,invalid if psalm_sensitive else None,0)

def spatial_grid(words,psalm_sensitive=False):
    total=sum(len(u) for u,_ in words); n=len(words)//128*128
    frags=[fragment(words[i:i+8],psalm_sensitive) for i in range(0,n,8)]
    ids=list(range(len(frags))); retained=sum(x[0] for x in frags)
    regions=[(st,min(st+128,len(frags))) for st in range(0,len(frags),128)]
    if not ids: return []
    def evaluate(order):
        sums=[[0]*3 for _ in range(2)]
        for k in range(0,len(order),16):
            pos=0; items=[]
            for idx in order[k:k+16]:
                length,its=frags[idx]; items.extend((t,pos+i) for t,i in its); pos+=length
            v=coverage_counts(pos,items)
            for m in range(2):
                for j in range(3): sums[m][j]+=v[m][j]
        return [[x/retained for x in row] for row in sums]
    obs=evaluate(ids); out=[]
    for control in ('local128','regional1024','whole_corpus'):
        vals=[]
        for rep in range(19):
            rng=random.Random(2026102601+rep); order=ids.copy()
            ranges=[(i,i+16) for i in range(0,len(ids),16)] if control=='local128' else regions if control=='regional1024' else [(0,len(ids))]
            for a,b in ranges:
                sub=order[a:b]; rng.shuffle(sub); order[a:b]=sub
            vals.append(evaluate(order))
        for mi,mode in enumerate(('exact','expanded')):
            for j,r in enumerate(RADII):
                vs=[v[mi][j] for v in vals]; mu=statistics.mean(vs)
                out.append({'mode':mode,'radius':r,'control':control,'blocks':len(ids)//16,
                            'retained_units':retained,'total_units':total,'retained_fraction':retained/total,
                            'observed':obs[mi][j],'null_mean':mu,'delta':obs[mi][j]-mu,
                            'null_min':min(vs),'null_max':max(vs)})
    return out

def primary_from_grids(cov,dist,spatial):
    c={r['mode']:r['mean'] for r in cov if r['block']==512 and r['offset']==0 and r['radius']==64}
    d={}
    for mode in ('exact','expanded'):
        cond=[]; complete=True
        for off in (0,640):
            for ph in (0,64):
                x={r['gap']:r for r in dist if r['mode']==mode and r['cap']==1024 and r['offset']==off and r['phase']==ph}
                if 0 not in x or 1024 not in x or x[0]['mean'] is None or x[1024]['mean'] is None:
                    complete=False; break
                cond.append(x[0]['mean']-x[1024]['mean'])
            if not complete: break
        d[mode]=statistics.mean(cond) if complete and len(cond)==4 else None
    s={}
    for control in ('local128','regional1024','whole_corpus'):
        s[control]={m:next(r['delta'] for r in spatial if r['control']==control and r['radius']==64 and r['mode']==m) for m in ('exact','expanded')}
    return {'coverage':c,'distance':d,'spatial':s}

def validate_primary(observed,expected,book):
    for metric in ('coverage','distance'):
        for mode in ('exact','expanded'):
            if not close(observed[metric][mode],expected[metric][mode]):
                raise AssertionError(f'{book} {metric}/{mode}: expected {expected[metric][mode]!r}, got {observed[metric][mode]!r}')
    for control in ('local128','regional1024','whole_corpus'):
        for mode in ('exact','expanded'):
            if not close(observed['spatial'][control][mode],expected['spatial'][control][mode]):
                raise AssertionError(f'{book} spatial {control}/{mode}: expected {expected["spatial"][control][mode]!r}, got {observed["spatial"][control][mode]!r}')

def aggregate_24(source_results,expected):
    by={r['source_book']:r for r in source_results}; groups={}
    for e in expected['source_books']: groups.setdefault(e['traditional_24_book'],[]).append(e['source_book'])
    out=[]
    for frozen in expected['reporting_24']:
        name=frozen['traditional_book']; comps=groups[name]
        if len(comps)==1:
            x=by[comps[0]]; p=x['primary']
            row={'traditional_book':name,'source_books':1,'components':comps,'words':x['word_count'],'sound_units':x['sound_unit_count'],
                 'coverage_exact':p['coverage']['exact'],'coverage_expanded':p['coverage']['expanded'],
                 'distance_exact':p['distance']['exact'],'distance_expanded':p['distance']['expanded'],
                 'spatial_local_exact':p['spatial']['local128']['exact'],'spatial_local_expanded':p['spatial']['local128']['expanded'],
                 'spatial_regional_exact':p['spatial']['regional1024']['exact'],'spatial_regional_expanded':p['spatial']['regional1024']['expanded'],
                 'spatial_whole_exact':p['spatial']['whole_corpus']['exact'],'spatial_whole_expanded':p['spatial']['whole_corpus']['expanded'],
                 'reporting_aggregation':'single source-book'}
        else:
            xs=[by[b] for b in comps]
            c={}
            for mode in ('exact','expanded'):
                num=den=0
                for x in xs:
                    rr=next(r for r in x['coverage_grid'] if r['mode']==mode and r['block']==512 and r['offset']==0 and r['radius']==64)
                    num+=rr['mean']*rr['blocks']; den+=rr['blocks']
                c[mode]=num/den
            d={}
            for mode in ('exact','expanded'):
                cond=[]
                for off in (0,640):
                    for ph in (0,64):
                        num=den=0
                        for x in xs:
                            rr0=next(r for r in x['distance_grid'] if r['mode']==mode and r['cap']==1024 and r['offset']==off and r['phase']==ph and r['gap']==0)
                            rr1=next(r for r in x['distance_grid'] if r['mode']==mode and r['cap']==1024 and r['offset']==off and r['phase']==ph and r['gap']==1024)
                            if rr0['blocks'] and rr0['mean'] is not None and rr1['mean'] is not None:
                                num+=(rr0['mean']-rr1['mean'])*rr0['blocks']; den+=rr0['blocks']
                        cond.append(num/den if den else None)
                d[mode]=statistics.mean([v for v in cond if v is not None]) if all(v is not None for v in cond) else None
            sp={}
            for control in ('local128','regional1024','whole_corpus'):
                sp[control]={}
                for mode in ('exact','expanded'):
                    num=den=0
                    for x in xs:
                        rr=next(r for r in x['spatial_grid'] if r['control']==control and r['radius']==64 and r['mode']==mode)
                        num+=rr['delta']*rr['retained_units']; den+=rr['retained_units']
                    sp[control][mode]=num/den
            row={'traditional_book':name,'source_books':len(comps),'components':comps,'words':sum(x['word_count'] for x in xs),'sound_units':sum(x['sound_unit_count'] for x in xs),
                 'coverage_exact':c['exact'],'coverage_expanded':c['expanded'],'distance_exact':d['exact'],'distance_expanded':d['expanded'],
                 'spatial_local_exact':sp['local128']['exact'],'spatial_local_expanded':sp['local128']['expanded'],
                 'spatial_regional_exact':sp['regional1024']['exact'],'spatial_regional_expanded':sp['regional1024']['expanded'],
                 'spatial_whole_exact':sp['whole_corpus']['exact'],'spatial_whole_expanded':sp['whole_corpus']['expanded'],
                 'reporting_aggregation':'pooled eligible source-book blocks/material; no cross-source motifs'}
        # compare frozen reporting row
        for k,v in frozen.items():
            if k in ('components','reporting_aggregation','traditional_book','source_books','words','sound_units'):
                if row[k]!=v: raise AssertionError(f'24-book {name} {k}: expected {v!r}, got {row[k]!r}')
            else:
                if not close(row[k],v): raise AssertionError(f'24-book {name} {k}: expected {v!r}, got {row[k]!r}')
        out.append(row)
    return out

def write_primary_csv(path,rows):
    fields=['source_book','git_blob_sha1','words','sound_units','coverage_exact','coverage_expanded','distance_exact','distance_expanded','spatial_local_exact','spatial_local_expanded','spatial_regional_exact','spatial_regional_expanded','spatial_whole_exact','spatial_whole_expanded']
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader()
        for x in rows:
            p=x['primary']; w.writerow({'source_book':x['source_book'],'git_blob_sha1':x['git_blob_sha1'],'words':x['word_count'],'sound_units':x['sound_unit_count'],
                'coverage_exact':p['coverage']['exact'],'coverage_expanded':p['coverage']['expanded'],'distance_exact':p['distance']['exact'],'distance_expanded':p['distance']['expanded'],
                'spatial_local_exact':p['spatial']['local128']['exact'],'spatial_local_expanded':p['spatial']['local128']['expanded'],
                'spatial_regional_exact':p['spatial']['regional1024']['exact'],'spatial_regional_expanded':p['spatial']['regional1024']['expanded'],
                'spatial_whole_exact':p['spatial']['whole_corpus']['exact'],'spatial_whole_expanded':p['spatial']['whole_corpus']['expanded']})

def write_24_csv(path,rows):
    fields=['traditional_book','source_books','components','words','sound_units','coverage_exact','coverage_expanded','distance_exact','distance_expanded','spatial_local_exact','spatial_local_expanded','spatial_regional_exact','spatial_regional_expanded','spatial_whole_exact','spatial_whole_expanded','reporting_aggregation']
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader()
        for x in rows:
            z=x.copy(); z['components']=' + '.join(z['components']); w.writerow(z)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-work',default=str(ROOT/'.local'/'tanakh'/'preparation')); ap.add_argument('--output-dir',default=str(ROOT/'.local'/'tanakh'/'primary'))
    args=ap.parse_args(); raw=Path(args.source_work).resolve()/'sources_raw'; outdir=Path(args.output_dir).resolve(); outdir.mkdir(parents=True,exist_ok=True)
    expected=load_json(ROOT/'config'/'tanakh'/'primary_expected.json'); freeze=load_json(ROOT/'config'/'tanakh'/'source_freeze.json')
    kwq=load_json(ROOT/'config'/'tanakh'/'ketiv_without_qere.json'); editorial=load_json(ROOT/'config'/'tanakh'/'editorial_repeat_tails.json')
    configs={'kwq':{r['ref']:r for r in kwq['rules']},'editorial':{r['ref']:r for r in editorial['rules']}}
    exp={r['source_book']:r for r in expected['source_books']}; results=[]
    for row in freeze['source_books']:
        book=row['source_book']; print(f"[{int(row['order']):02d}/39] {book} ...",flush=True)
        sounds,words,invalid=prepare_stream(row,raw,configs)
        if len(words)!=exp[book]['word_count'] or len(sounds)!=exp[book]['sound_unit_count']: raise AssertionError(f'primary count mismatch for {book}')
        cov=coverage_grid(sounds,invalid); dist=distance_grid(sounds,invalid); sp=spatial_grid(words,book=='Psalms'); primary=primary_from_grids(cov,dist,sp)
        validate_primary(primary,exp[book]['primary'],book)
        results.append({'order':row['order'],'source_book':book,'traditional_24_book':row['traditional_24_book'],'git_blob_sha1':row['git_blob_sha1'],
                        'word_count':len(words),'sound_unit_count':len(sounds),'primary':primary,'coverage_grid':cov,'distance_grid':dist,'spatial_grid':sp})
    reporting=aggregate_24(results,expected)
    (outdir/'source_books_full_grid.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (outdir/'traditional_24_primary.json').write_text(json.dumps(reporting,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    write_primary_csv(outdir/'source_books_primary.csv',results); write_24_csv(outdir/'traditional_24_primary.csv',reporting)
    status={'status':'PASS','source_books':39,'traditional_books':24,'words':sum(x['word_count'] for x in results),'sound_units':sum(x['sound_unit_count'] for x in results),
            'detail':'Primary grid reproduced from frozen inputs; all frozen source-book and 24-book primary values match.'}
    (outdir/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS primary primary analysis: 39/39 source-books / 24 reporting books')
    print('PASS source/count continuity and frozen primary regression')
    print('Aramaic-span exclusion sensitivity is a separate analysis and does not redefine the primary corpus.')
if __name__=='__main__': main()
