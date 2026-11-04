"""Rebuild article analysis streams from the frozen inputs distributed with this release.

Biblical readings are regenerated from the frozen Sefaria verse inputs and checked against the
included prepared texts. Modern readings use the frozen prepared vocalized layers that served as
the article inputs. Raw external-service responses and online diacritization are intentionally
outside the public reproduction workflow.
"""
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/core'))
sys.path.insert(0,str(ROOT/'src/preparation'))
from phonetic_core_v2 import transliterate_word
from prepare_biblical_reading import adapt
TOKEN=re.compile(r'[א-ת][א-ת\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]*')

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def main():
    cfg=json.loads((ROOT/'config/corpora.json').read_text(encoding='utf-8'))
    expected_texts=json.loads((ROOT/'config/prepared_texts.json').read_text(encoding='utf-8'))
    for name,digest in expected_texts.items():
        p=ROOT/name
        if not p.is_file() or sha_bytes(p.read_bytes())!=digest:
            raise ValueError('Frozen prepared text differs: '+name)

    segments=[];readings=[];passports=[]
    # Biblical sources: regenerate the deterministic reading and verify the frozen prepared copy.
    for book in cfg['biblical']:
        source=ROOT/f'sources/original/biblical/{book}_verses.json'
        vs=json.loads(source.read_text(encoding='utf-8'))['verses'];seq=[];rows=[]
        for v in vs:
            text,edits,spans=adapt(v['source_text']);words=[];units=[]
            for m in TOKEN.finditer(text):
                u=transliterate_word(m.group(),return_units=True)
                if not u: raise ValueError('Unresolved biblical token: '+v['ref'])
                words.append(''.join(u));units+=u
            seq+=units
            rows.append(dict(ref=v['ref'],source=v['source_text'],text=text,edits=edits))
            readings.append(dict(ref=v['ref'],readings=words,sounds=units))
        frozen_text=(ROOT/f'sources/prepared/{book}/text.txt').read_text(encoding='utf-8')
        generated='\n'.join(v['text'] for v in rows)+'\n'
        if generated!=frozen_text: raise ValueError('Prepared biblical text differs: '+book)
        frozen_changes=json.loads((ROOT/f'sources/prepared/{book}/changes.json').read_text(encoding='utf-8'))
        if rows!=frozen_changes: raise ValueError('Prepared biblical change log differs: '+book)
        name=vs[0]['ref'].split()[0]
        segments.append(dict(corpus=name,segment=0,sounds=seq))
        passports.append(dict(corpus=name,source=str(source.relative_to(ROOT)),source_sha256=sha_bytes(source.read_bytes()),verses=len(vs),segments=1,units=len(seq),vocalization='source',qere_edits=sum(len(v['edits']) for v in rows)))

    # Modern sources: use frozen prepared vocalized layers. These are the actual article inputs.
    for ident,slug in cfg['modern'].items():
        source=ROOT/f'sources/prepared/{slug}/text.txt'
        meta_path=ROOT/f'sources/prepared/{slug}/changes.json'
        text=source.read_text(encoding='utf-8'); meta=json.loads(meta_path.read_text(encoding='utf-8'))
        if sha_bytes(source.read_bytes())!=meta['output_sha256']:
            raise ValueError('Prepared modern reading hash differs: '+slug)
        bounds=sorted({0,len(text)}|{b['offset'] for b in meta['boundaries']});segs=[];seq=[];unknown=[]
        def flush():
            nonlocal seq
            if seq: segs.append(dict(corpus='modern_'+ident,segment=len(segs),sounds=seq)); seq=[]
        for a,b in zip(bounds,bounds[1:]):
            for m in TOKEN.finditer(text[a:b]):
                u=transliterate_word(m.group(),return_units=True)
                if not u:
                    unknown.append(dict(start=a+m.start(),end=a+m.end(),text=m.group())); flush()
                else: seq+=u
            flush()
        frozen_unknown=json.loads((ROOT/f'sources/prepared/{slug}/unresolved.json').read_text(encoding='utf-8'))
        if unknown!=frozen_unknown: raise ValueError('Unresolved-token inventory differs: '+slug)
        segments+=segs
        raw=ROOT/f'sources/original/modern/{slug}.txt'
        passports.append(dict(corpus='modern_'+ident,name=slug,source=str(raw.relative_to(ROOT)),source_sha256=sha_bytes(raw.read_bytes()),reading_sha256=sha_bytes(source.read_bytes()),segments=len(segs),units=sum(len(s['sounds']) for s in segs),unresolved_tokens=len(unknown),vocalization=meta['source_kind'],removed_carriers=len(meta['edits']),vocalization_certified=False))

    expected=json.loads((ROOT/'reference/segments.json').read_text(encoding='utf-8'))
    write_json(ROOT/'results/corpus/passports.json',passports)
    write_json(ROOT/'results/corpus/segments.json',segments)
    write_json(ROOT/'results/corpus/readings.json',readings)
    if segments!=expected:
        write_json(ROOT/'results/corpus/status.json',{'status':'DIFFERENCE','detail':'Rebuilt streams differ from the frozen reference. Analyses stopped.'})
        raise ValueError('Corpus differs from the frozen reference; inspect results/corpus. No reference replacement performed.')
    write_json(ROOT/'results/corpus/status.json',{'status':'PASS','detail':'All 10 streams rebuilt from frozen article inputs and match the frozen reference exactly. Technical verification; not linguistic certification.'})
    print('PASS: all 10 article corpora rebuilt from frozen inputs and match the frozen reference exactly',flush=True)
if __name__=='__main__': main()
