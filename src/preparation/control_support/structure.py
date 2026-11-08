"""Apply reviewed internal annotations to the unchanged outer body."""
import json
from pathlib import Path
from extract import ROOT,extract

def process(raw,spec,annotations):
 body,audit=extract(raw,spec)
 cursor=spec['start'];text=raw.decode('utf-8');pieces=[];events=[]
 for ann in sorted(annotations,key=lambda x:x['start']):
  a,b=ann['start'],ann['end']
  if not cursor<=a<b<=spec['end'] or text[a:b]!=ann['text']:raise ValueError('Invalid annotation')
  pieces.append(text[cursor:a]);offset=sum(map(len,pieces))
  replacement='' if ann['kind']=='note_reference' else '\n\n'
  pieces.append(replacement)
  events.append(dict(ann,output_offset=offset,replacement=replacement))
  cursor=b
 pieces.append(text[cursor:spec['end']]);clean=''.join(pieces)
 # Reverse every edit, then reconstruct the complete source.
 restored=clean
 for e in reversed(events):
  p=e['output_offset'];restored=restored[:p]+e['text']+restored[p+len(e['replacement']):]
 if restored!=body:raise ValueError('Reconstruction failed')
 return clean,dict(audit,internal_edits=events,review_status='pilot_structural_annotations_applied')
