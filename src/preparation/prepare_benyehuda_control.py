"""Deterministic structural extraction and whitespace preparation; no API calls."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent/'control_support'))
from structure import process

def save(path,text):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(text.encode('utf-8'))
def js(path,obj):save(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def prepare(text):
 # Preserve every nonempty source line and its exact content. Only blank runs change.
 spans=list(re.finditer(r'[^\n]*\S[^\n]*',text))
 parts=[];records=[];pos=0
 for i,m in enumerate(spans):
  gap=text[spans[i-1].end():m.start()] if i else ''
  sep=('\n\n' if gap.count('\n')>=2 else '\n') if i else ''
  parts.append(sep);pos+=len(sep)
  records.append({'source_start':m.start(),'source_end':m.end(),'start':pos,'end':pos+len(m[0]),'preceding_newlines':gap.count('\n')})
  parts.append(m[0]);pos+=len(m[0])
 out=''.join(parts)+'\n'
 if re.sub(r'\s','',out)!=re.sub(r'\s','',text):raise ValueError('Content changed')
 return out,records

def main():
 cfg=ROOT/'protocols/modern_control';base=ROOT/'data/data_processed/modern/benyehuda'
 anns=json.loads((cfg/'annotations.json').read_text(encoding='utf-8'))
 summary=[]
 for spec in json.loads((cfg/'boundaries.json').read_text(encoding='utf-8')):
  id=spec['id'];raw=(ROOT/'data/data_raw/modern/benyehuda'/f'{id}.txt').read_bytes()
  body,audit=process(raw,spec,anns[id]);clean,lines=prepare(body)
  bounds=[]
  for e in audit['internal_edits']:
   if e['kind']=='note_reference':continue
   following=next((r['start'] for r in lines if r['source_start']>=e['output_offset']),len(clean))
   bounds.append({'offset':following,'kind':e['kind'],'label':e['text']})
  save(base/'cleaned'/f'{id}.txt',clean)
  js(base/'audit'/f'{id}.json',audit)
  meta={'id':id,'sha256':hashlib.sha256(clean.encode()).hexdigest(),'offset_unit':'Unicode codepoints','lines':lines,'boundaries':bounds,'line_source':'structurally extracted text before whitespace preparation','status':'structural preparation only; language review and phonetic conversion pending'}
  js(base/'cleaned'/f'{id}.json',meta)
  if id!='884':
   save(base/'nakdan_input'/f'{id}.txt',clean)
   js(base/'nakdan_input'/f'{id}.json',meta)
  summary.append({'id':id,'characters':len(clean),'nonempty_lines':len(lines),'structural_boundaries':len(bounds),'nakdan_candidate':id!='884'})
 js(base/'preparation_summary.json',summary)
 print(json.dumps(summary))
if __name__=='__main__':main()
