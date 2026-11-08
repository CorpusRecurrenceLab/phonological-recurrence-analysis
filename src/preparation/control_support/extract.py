"""Reproduce reviewed outer body boundaries; no phonetic normalization."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def extract(raw, spec):
    if hashlib.sha256(raw).hexdigest()!=spec['sha256']:
        raise ValueError('Source checksum mismatch: '+spec['id'])
    text=raw.decode('utf-8')
    a,b=spec['start'],spec['end']
    if not (0<=a<b<=len(text)):raise ValueError('Invalid boundaries')
    if text[a:a+len(spec['start_anchor'])]!=spec['start_anchor']:raise ValueError('Start mismatch')
    if text[b:b+len(spec['end_anchor'])]!=spec['end_anchor']:raise ValueError('End mismatch')
    body=text[a:b]
    audit={'id':spec['id'],'status':spec['status'],'excluded':[{'start':0,'end':a,'reason':'front matter; reviewed outer boundary','text':text[:a]},{'start':b,'end':len(text),'reason':'date/notes/service footer; reviewed outer boundary','text':text[b:]}]}
    assert audit['excluded'][0]['text']+body+audit['excluded'][1]['text']==text
    return body,audit
