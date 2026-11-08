"""Offline request preparation. Does not contact Nakdan or require a key."""
import hashlib,json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/data_processed/modern/benyehuda'
LIMIT=24000

def digest(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(s.encode('utf-8'))
def dump(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def split_ranges(text,limit=LIMIT):
 start=0
 while start<len(text):
  end=min(start+limit,len(text))
  if end<len(text):
   cut=text.rfind('\n\n',start,end)
   if cut>start:end=cut+2
   else:
    spaces=list(re.finditer(r'\s+',text[start:end]))
    if not spaces:raise ValueError('No safe whitespace boundary within limit')
    end=start+spaces[-1].end()
  yield start,end
  start=end

def main():
 report=[]
 for id in ['523','7924','884']:
  source=(BASE/'cleaned'/f'{id}.txt').read_text(encoding='utf-8')
  meta=json.loads((BASE/'cleaned'/f'{id}.json').read_text(encoding='utf-8'))
  if digest(source)!=meta['sha256']:raise ValueError('Cleaned file changed: '+id)
  # Only canonical normalization: presentation forms with canonical decompositions.
  normalized=unicodedata.normalize('NFC',source)
  lines=[dict(r,start=len(unicodedata.normalize('NFC',source[:r['start']])),end=len(unicodedata.normalize('NFC',source[:r['end']]))) for r in meta['lines']]
  for old,new in zip(meta['lines'],lines):
   if normalized[new['start']:new['end']]!=unicodedata.normalize('NFC',source[old['start']:old['end']]):raise ValueError('Line mapping failed')
  bounds=[dict(b,offset=len(unicodedata.normalize('NFC',source[:b['offset']]))) for b in meta['boundaries']]
  foreign=[{'start':m.start(),'end':m.end(),'text':m[0],'context':normalized[max(0,m.start()-60):m.end()+60],'status':'script flag, not automatic language classification'} for m in re.finditer(r'[A-Za-z\u0400-\u04ff]+(?:[ -]+[A-Za-z\u0400-\u04ff]+)*',normalized)]
  presentation={c:source.count(c) for c in sorted(set(source)) if '\ufb1d'<=c<='\ufb4f'}
  dump(BASE/'audit'/f'{id}_language_unicode.json',{'source_sha256':digest(source),'normalized_sha256':digest(normalized),'presentation_forms':presentation,'script_flags':foreign,'limitation':'Does not detect Yiddish or Aramaic written in Hebrew script. Full language review is pending.'})
  write(BASE/'normalized'/f'{id}.txt',normalized)
  dump(BASE/'normalized'/f'{id}.json',{'sha256':digest(normalized),'normalization':'NFC','boundaries':bounds,'lines':lines,'offset_unit':'Unicode codepoints','source':'cleaned/'+id+'.txt','phonetic_analysis_ready':False})
  if id=='884':
   report.append({'id':id,'chunks':0,'status':'original vocalization retained; no API request planned'});continue
  # Preserve the partly vocalized input. Stripping policy must follow actual API docs.
  ends=sorted(set([0,len(normalized)]+[b['offset'] for b in bounds]))
  chunks=[];parts=[]
  for section,(a,b) in enumerate(zip(ends,ends[1:])):
   for lo,hi in split_ranges(normalized[a:b]):
    start,end=a+lo,a+hi;part=normalized[start:end]
    name=f'{len(chunks)+1:04d}.txt'
    chunks.append({'file':name,'start':start,'end':end,'characters':len(part),'sha256':digest(part),'section':section});parts.append(part)
  if ''.join(parts)!=normalized:raise ValueError('Reassembly failed')
  if any(len(p)>LIMIT or len(p.encode('utf-16-le'))//2>30000 for p in parts):raise ValueError('Oversize chunk')
  destination=BASE/'nakdan_batches'/id
  expected={c['file'] for c in chunks}
  unexpected={p.name for p in destination.glob('*.txt')}-expected
  if unexpected:raise ValueError('Unexpected batch files; move them aside before rebuilding: '+str(sorted(unexpected)))
  for c,part in zip(chunks,parts):write(destination/c['file'],part)
  dump(BASE/'nakdan_batches'/id/'manifest.json',{'id':id,'source_sha256':digest(normalized),'limit':LIMIT,'chunks':chunks,'status':'offline prepared; NOT sent; language review and API schema integration pending','preserve_existing_marks':True})
  report.append({'id':id,'chunks':len(chunks),'max_characters':max(map(len,parts)),'script_flags':len(foreign)})
 dump(BASE/'batch_summary.json',report);print(json.dumps(report))
if __name__=='__main__':main()
