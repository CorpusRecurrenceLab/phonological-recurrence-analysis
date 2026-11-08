"""Fixed poetic-comparator and different-surface-word controls.

The module evaluates three
preselected Biblical poetic comparators (Psalms, Job, Song of Songs) and an
exact-mode lexical sensitivity in which matching motif tokens must have
different phonological surface-word hosts.
"""
from __future__ import annotations
import bisect,csv,hashlib,json,random,statistics,sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'src'))
sys.path.insert(0,str(P/'src/core'))
sys.path.insert(0,str(P/'src/preparation'))
from prepare import TOKEN
from phonetic_core_v2 import transliterate_word
from prepare_biblical_reading import adapt
from analysis.compare_modes import PAIRS, NEAR, variants, similarity, RADII
from analysis.spatial import corpus_words

V=set('aeiou')
NEW=(('Psalms','psalms'),('Job','job'),('Song_of_Songs','song_of_songs'))


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def load_new_book(label,slug):
    d=json.loads((P/f'sources/variants/biblical/{slug}_verses.json').read_text(encoding='utf-8'))
    chapters=defaultdict(list)
    for v in d['verses']:
        text,_,_=adapt(v['source_text']); ws=[]
        for m in TOKEN.finditer(text):
            u=transliterate_word(m.group(),return_units=True)
            if not u: raise ValueError(f"Unresolved token in {v['ref']}: {m.group()}")
            ws.append(tuple(u))
        chapters[v['chapter']].extend(ws)
    if label=='Psalms':
        words=[]; hard=set(); pos=0
        for ch in range(1,d['chapter_count']+1):
            cw=chapters[ch]
            if words: hard.add(len(words))  # boundary before next psalm's first word
            words.extend(cw)
        return {'corpus':label,'segments':[words],'hard_word_boundaries':[hard],'source':d}
    words=[]
    for ch in range(1,d['chapter_count']+1):words.extend(chapters[ch])
    return {'corpus':label,'segments':[words],'hard_word_boundaries':[set()],'source':d}


def flattened(words):
    sounds=[]; unit_word=[]
    for wi,w in enumerate(words):
        sounds.extend(w);unit_word.extend([wi]*len(w))
    return sounds,unit_word


def motif_occurrences(words,hard_word_boundaries=frozenset()):
    sounds,unit_word=flattened(words); out=[]
    for i in range(len(sounds)-2):
        t=tuple(sounds[i:i+3])
        if not 0<sum(x in V for x in t)<3: continue
        wis=unit_word[i:i+3]
        lo,hi=min(wis),max(wis)
        if any(b>lo and b<=hi for b in hard_word_boundaries): continue
        host=tuple(words[j] for j in dict.fromkeys(wis))
        out.append((t,i,host))
    return sounds,out


def nearest(ps,i):
    k=bisect.bisect_right(ps,i-3);best=i-ps[k-1] if k else 10**9;k=bisect.bisect_left(ps,i+3)
    return min(best,ps[k]-i if k<len(ps) else 10**9)


def coverage_counts(length,items,require_different_host=False,expanded=False):
    # items: (motif,start,host). Search is bounded by the largest declared radius.
    occ=defaultdict(list)
    for t,i,h in items: occ[t].append((i,h))
    positions={t:[x[0] for x in rows] for t,rows in occ.items()}
    marks=[bytearray(length) for _ in RADII]; rmax=max(RADII)
    for t,rows in occ.items():
        candidates=[t]
        if expanded:candidates += [v for v in variants(t) if v in occ]
        for i,h in rows:
            best=rmax+1
            for typ in candidates:
                rr=occ.get(typ,()); ps=positions.get(typ,())
                lo=bisect.bisect_left(ps,i-rmax);hi=bisect.bisect_right(ps,i+rmax)
                for j,h2 in rr[lo:hi]:
                    d=abs(i-j)
                    if d<3 or (require_different_host and h==h2):continue
                    if d<best:best=d
            for k,r in enumerate(RADII):
                if best<=r:marks[k][i:i+3]=b'\1\1\1'
    return [sum(x) for x in marks]


def slice_items(items,start,end):
    return [(t,i-start,h) for t,i,h in items if i>=start and i+3<=end]


def compute_new_coverage(corpus):
    rows=[]; density=[]; total=0
    prepared=[]
    for words,hard in zip(corpus['segments'],corpus['hard_word_boundaries']):
        sounds,items=motif_occurrences(words,hard);prepared.append((sounds,items));total+=len(sounds)
    for L in (512,1280):
      for offset in (0,L//2):
       vals=defaultdict(list);global_start=0
       for si,(sounds,items) in enumerate(prepared):
        for start in range(offset,len(sounds)-L+1,L):
         part=slice_items(items,start,start+L)
         for mode,expanded in (('exact',False),('expanded',True)):
          cc=coverage_counts(L,part,False,expanded)
          for k,r in enumerate(RADII):
           v=cc[k]/L;vals[mode,r].append(v)
           if L==512 and offset==0 and r==64:density.append(dict(corpus=corpus['corpus'],mode=mode,segment=si,start=global_start+start,length=L,coverage=v))
        global_start+=len(sounds)
       for (mode,r),vs in vals.items():
        ss=sorted(vs);rows.append(dict(corpus=corpus['corpus'],mode=mode,block=L,offset=offset,radius=r,blocks=len(vs),retained_fraction=len(vs)*L/total,mean=statistics.mean(vs),p10=ss[int((len(ss)-1)*.1)],median=statistics.median(vs),p90=ss[int((len(ss)-1)*.9)],minimum=min(vs)))
    return rows,density


def compute_new_distance(corpus):
    rows=[];detail=[]; total=0; prepared=[]
    for words,hard in zip(corpus['segments'],corpus['hard_word_boundaries']):
        sounds,items=motif_occurrences(words,hard);prepared.append((sounds,items));total+=len(sounds)
    for cap,L in ((256,512),(1024,1280),(4096,4352)):
      gaps=[g for g in (0,64,256,1024,4096) if g<=cap]
      for offset in (0,L//2):
       for phase in (0,64):
        blocks=defaultdict(list);anchors=0
        for si,(sounds,items) in enumerate(prepared):
         item_positions=[p for t,p,h in items]
         @lru_cache(None)
         def motifs(i):
          lo=bisect.bisect_left(item_positions,i);hi=bisect.bisect_right(item_positions,i+61)
          return {items[k][0] for k in range(lo,hi)}
         for start in range(offset,len(sounds)-L+1,L):
          vals=defaultdict(list)
          for i in range(start+phase,start+L-128-cap+1,128):
           anchors+=1
           for gap in gaps:
            scores=similarity(motifs(i),motifs(i+64+gap))
            for m,mode in enumerate(('exact','expanded')): vals[mode,gap].append(scores[m])
          for (mode,gap),vs in vals.items():
           mean=statistics.mean(vs);blocks[mode,gap].append(mean);detail.append(dict(corpus=corpus['corpus'],mode=mode,cap=cap,offset=offset,phase=phase,segment=si,start=start,gap=gap,mean=mean))
         motifs.cache_clear()
        for (mode,gap),vs in blocks.items(): rows.append(dict(corpus=corpus['corpus'],mode=mode,cap=cap,block=L,offset=offset,phase=phase,gap=gap,blocks=len(vs),anchors=anchors,retained_fraction=len(vs)*L/total,mean=statistics.mean(vs)))
    return rows,detail


def fragment(words,hard_global,base):
    # base = global word index for this 8-word fragment in the segment.
    sounds,unit_word=flattened(words); items=[]
    local_hard={b-base for b in hard_global if base<b<base+len(words)}
    for i in range(len(sounds)-2):
        t=tuple(sounds[i:i+3])
        if not 0<sum(x in V for x in t)<3:continue
        wis=unit_word[i:i+3];lo,hi=min(wis),max(wis)
        if any(b>lo and b<=hi for b in local_hard):continue
        host=tuple(words[j] for j in dict.fromkeys(wis));items.append((t,i,host))
    return len(sounds),items


def spatial_evaluate(frags,order,different=False,expanded=False):
    sums=[0]*3;units=0
    for k in range(0,len(order),16):
        pos=0;items=[]
        for idx in order[k:k+16]:
            length,its=frags[idx];items.extend((t,pos+i,h) for t,i,h in its);pos+=length
        cc=coverage_counts(pos,items,different,expanded)
        sums=[a+b for a,b in zip(sums,cc)];units+=pos
    return [x/units for x in sums]


def make_frags(wordsegs,hardsets):
    frags=[];regions=[];total=sum(len(w) for s in wordsegs for w in s)
    for seg,hard in zip(wordsegs,hardsets):
      first=len(frags);n=len(seg)//128*128
      frags.extend(fragment(seg[i:i+8],hard,i) for i in range(0,n,8))
      for st in range(first,len(frags),128):regions.append((st,min(st+128,len(frags))))
    return frags,regions,total


def compute_spatial_for(c,wordsegs,hardsets,modes=(('exact',False,False),('expanded',False,True))):
    frags,regions,total=make_frags(wordsegs,hardsets);ids=list(range(len(frags)));units=sum(x[0] for x in frags)
    rows=[];reps=[]
    observed={name:spatial_evaluate(frags,ids,diff,exp) for name,diff,exp in modes}
    for control in ('local128','regional1024','whole_corpus'):
      per={name:[] for name,_,_ in modes}
      for rep in range(19):
        rng=random.Random(2026102601+rep);order=ids.copy();ranges=[(i,i+16) for i in range(0,len(ids),16)] if control=='local128' else regions if control=='regional1024' else [(0,len(ids))]
        for a,b in ranges:
          sub=order[a:b];rng.shuffle(sub);order[a:b]=sub
        assert sorted(order)==ids
        for name,diff,exp in modes:
          v=spatial_evaluate(frags,order,diff,exp);per[name].append(v)
          for j,r in enumerate(RADII):reps.append(dict(corpus=c,condition=name,radius=r,control=control,replicate=rep,coverage=v[j]))
      for name,_,_ in modes:
       for j,r in enumerate(RADII):
        vs=[x[j] for x in per[name]];mu=statistics.mean(vs);rows.append(dict(corpus=c,condition=name,radius=r,control=control,blocks=len(ids)//16,retained_fraction=units/total,observed=observed[name][j],null_mean=mu,delta=observed[name][j]-mu,null_min=min(vs),null_max=max(vs)))
    return rows,reps


def distributed_wordsets(newbooks):
    old=corpus_words(additional=False)
    out={c:(segs,[set() for _ in segs]) for c,segs in old.items()}
    for b in newbooks:out[b['corpus']]=(b['segments'],b['hard_word_boundaries'])
    return out


def compute_different_surface_coverage(wordsets):
    out=[]
    for c,(segs,hards) in wordsets.items():
      prepared=[];total=0
      for words,hard in zip(segs,hards):
        sounds,items=motif_occurrences(words,hard);prepared.append((sounds,items));total+=len(sounds)
      for L in (512,1280):
       for offset in (0,L//2):
        vals=defaultdict(list)
        for sounds,items in prepared:
         for start in range(offset,len(sounds)-L+1,L):
          part=slice_items(items,start,start+L)
          for condition,diff in (('baseline_exact',False),('different_surface_word',True)):
           cc=coverage_counts(L,part,diff,False)
           for k,r in enumerate(RADII):vals[condition,r].append(cc[k]/L)
        for (condition,r),vs in vals.items():out.append(dict(corpus=c,condition=condition,block=L,offset=offset,radius=r,blocks=len(vs),retained_fraction=len(vs)*L/total,mean=statistics.mean(vs),median=statistics.median(vs)))
    return out


def extension_signature():
    h=hashlib.sha256()
    h.update(Path(__file__).read_bytes())
    h.update((P/'protocols/poetic_comparators.md').read_bytes())
    for q in sorted((P/'sources/variants/biblical').glob('*.json')):h.update(q.read_bytes())
    return h.hexdigest()


def checkpoint_path(kind,name):
    q=P/'.local/extension_checkpoints'/kind/f'{name}.json';q.parent.mkdir(parents=True,exist_ok=True);return q


def main():
    newbooks=[load_new_book(*x) for x in NEW]
    signature=extension_signature()
    inventory=[]
    for b in newbooks:
      units=sum(len(w) for s in b['segments'] for w in s)
      inventory.append(dict(corpus=b['corpus'],chapters=b['source']['chapter_count'],verses=b['source']['verse_count'],words=sum(map(len,b['segments'])),sound_units=units,hard_internal_boundaries=sum(map(len,b['hard_word_boundaries'])),version_title=b['source']['version_title'],version_source=b['source']['version_source']))
    outdir=P/'results/controls';outdir.mkdir(parents=True,exist_ok=True)
    write_csv(outdir/'poetic_comparator_inventory.csv',inventory)

    cov=[];dens=[];dist=[];db=[];sp=[];spr=[]
    for b in newbooks:
      cp=checkpoint_path('comparators',b['corpus'])
      data=json.loads(cp.read_text(encoding='utf-8')) if cp.exists() else {}
      if data.get('_signature')==signature:
        print(b['corpus'],'comparison checkpoint',flush=True)
      else:
        print(b['corpus'],'comparison calculating',flush=True)
        a,z=compute_new_coverage(b);dd,zz=compute_new_distance(b);ss,rr=compute_spatial_for(b['corpus'],b['segments'],b['hard_word_boundaries'])
        data={'_signature':signature,'coverage':a,'density':z,'distance':dd,'distance_blocks':zz,'spatial':ss,'spatial_replicates':rr};write_json(cp,data)
      cov+=data['coverage'];dens+=data['density'];dist+=data['distance'];db+=data['distance_blocks'];sp+=data['spatial'];spr+=data['spatial_replicates']
    write_csv(outdir/'poetic_coverage.csv',cov);write_csv(outdir/'poetic_density.csv',dens);write_csv(outdir/'poetic_distance.csv',dist);write_csv(outdir/'poetic_distance_blocks.csv',db);write_csv(outdir/'poetic_spatial.csv',sp);write_csv(outdir/'poetic_spatial_replicates.csv',spr)

    wordsets=distributed_wordsets(newbooks)
    dcov=[]
    for c,pair in wordsets.items():
      cp=checkpoint_path('word_coverage',c)
      data=json.loads(cp.read_text(encoding='utf-8')) if cp.exists() else {}
      if data.get('_signature')==signature:
        rows=data['rows'];print(c,'different-surface coverage checkpoint',flush=True)
      else:
        print(c,'different-surface coverage calculating',flush=True);rows=compute_different_surface_coverage({c:pair});write_json(cp,{'_signature':signature,'rows':rows})
      dcov+=rows
    write_csv(outdir/'different_surface_coverage.csv',dcov)
    dsp=[];dspr=[]
    for c,(segs,hards) in wordsets.items():
      cp=checkpoint_path('word_spatial',c)
      data=json.loads(cp.read_text(encoding='utf-8')) if cp.exists() else {}
      if data.get('_signature')==signature:
        print(c,'different-surface spatial checkpoint',flush=True)
      else:
        print(c,'different-surface spatial calculating',flush=True)
        a,z=compute_spatial_for(c,segs,hards,modes=(('baseline_exact',False,False),('different_surface_word',True,False)));data={'_signature':signature,'spatial':a,'replicates':z};write_json(cp,data)
      dsp+=data['spatial'];dspr+=data['replicates']
    write_csv(outdir/'different_surface_spatial.csv',dsp);write_csv(outdir/'different_surface_spatial_replicates.csv',dspr)

    psrc=P/'sources/variants/biblical'
    meta={
      'status':'PASS','baseline_repository_commit':'a58c44c650bea66f73398ae05c2542b74835566e',
      'preselected_poetic_comparators':['Psalms','Job','Song of Songs'],
      'different_surface_corpora':list(wordsets),
      'nonredistributed_works_excluded_from_word_control':['rivlin_ali_baba','bialik_beir_haharegah'],
      'psalms_policy':'one canonical stream; mixed triplets crossing psalm boundaries are prohibited',
      'analysis_signature':signature,
      'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'protocol_sha256':hashlib.sha256((P/'protocols/poetic_comparators.md').read_bytes()).hexdigest(),
      'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(psrc.glob('*.json'))},
      'outputs':{}
    }
    for p in sorted(outdir.glob('*.csv')):meta['outputs'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    # Recomputed provenance can differ from pinned metadata after a code or
    # documentation reorganization. Preserve the immutable release record and
    # verify the computed output hashes instead of overwriting that record.
    frozen=json.loads((outdir/'controls_validation.json').read_text(encoding='utf-8'))
    if meta['outputs'] != frozen['outputs']:
        raise ValueError('Recomputed extension outputs differ from frozen release hashes')
    write_json(P/'.local/validation/extension_metadata_generated.json',meta)
    print('PASS poetic comparators:',len(newbooks),'poetic comparators;',len(wordsets),'different-surface corpora')

if __name__=='__main__':main()
