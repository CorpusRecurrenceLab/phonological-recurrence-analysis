"""Sequential acquisition only; never certifies readings or modifies sources."""
import getpass,json,os,time,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlsplit
from dicta_control_pilot import ROOT, PARAMS, sha, render

def save(p, obj):
    q=p.with_suffix(p.suffix+'.part')
    q.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    q.replace(p)

def audit(source, response):
    text,changes=render(source,response)
    flags=[]
    offset=0
    for i,t in enumerate(response['data']):
        reasons=[]
        if not t['sep']:
            opt=t['nakdan']['options'][0]; w=opt['w']; morph=opt.get('morph',0)
            if isinstance(morph,int):
                if morph & 0x1f0000 in (0xb0000,0xc0000,0x110000,0x170000,0x180000,0x190000):reasons.append('morphology_review')
                if morph & 0x20000000000:reasons.append('aramaic_flag')
            if any(c in t['str'] for c in ('"','\u05f4')):reasons.append('internal_quote_candidate')
            if not any(c in w for c in '\u05b0\u05b1\u05b2\u05b3\u05b4\u05b5\u05b6\u05b7\u05b8\u05b9\u05ba\u05bb\u05bc\u05c7'):reasons.append('no_vocalic_or_shuruk_mark')
        elif any('\u05d0'<=c<='\u05ea' for c in t['str']):reasons.append('hebrew_in_separator')
        if reasons:flags.append(dict(token=i,source_start=offset,source=t['str'],reasons=reasons))
        offset+=len(t['str'])
    return text,dict(letter_changes=changes,review_flags=flags,status='REVIEW_REQUIRED')

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--send',action='store_true');ap.add_argument('--retry-unfinished',action='store_true',help='Explicitly retry requests with no saved response; preserve prior metadata');a=ap.parse_args()
    base=ROOT/'data/data_processed/modern/benyehuda';out=base/'nakdan_output';out.mkdir(exist_ok=True)
    jobs=[]
    for wid in ('523','7924'):
        folder=base/'nakdan_batches'/wid;m=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        for ch in m['chunks']:
            data=(folder/ch['file']).read_bytes()
            if sha(data)!=ch['sha256']:raise ValueError('Source hash mismatch')
            s=data.decode('utf-8')
            if len(s.encode('utf-16-le'))//2>30000:raise ValueError('Chunk too long')
            jobs.append((wid,ch,s))
    print('Validated input chunks:',len(jobs),'(884 excluded)')
    if not a.send:return
    lock=out/'active.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    key=url=None
    try:
        summary=[]
        for wid,ch,s in jobs:
            fingerprint=sha(s.encode()+json.dumps(PARAMS,sort_keys=True).encode())[:16]
            dest=out/wid/fingerprint;dest.mkdir(parents=True,exist_ok=True)
            response=dest/'response.json';meta=dest/'request.json'
            if not response.exists() and wid=='523' and ch['file']=='0001.txt':
                pilot=base/'nakdan_pilot'/fingerprint
                if (pilot/'response.json').exists():
                    review=json.loads((pilot/'review.json').read_text(encoding='utf-8'))
                    raw=(pilot/'response.json').read_bytes()
                    if review['parameters']!=PARAMS or review['input_sha256']!=ch['sha256'] or review['response_sha256']!=sha(raw):raise ValueError('Pilot provenance mismatch')
                    render(s,json.loads(raw));save(meta,dict(input_sha256=ch['sha256'],parameters=PARAMS,response_sha256=sha(raw),origin='pilot'))
                    response.write_bytes(raw)
            if not response.exists():
                if meta.exists():
                    if not a.retry_unfinished:raise ValueError('Unfinished request: '+str(dest)+'. Use recovery runner for an explicit retry.')
                    old=json.loads(meta.read_text(encoding='utf-8'))
                    if old.get('input_sha256')!=ch['sha256'] or old.get('parameters')!=PARAMS:raise ValueError('Unfinished request provenance mismatch')
                    history=dest/'attempt_history';history.mkdir(exist_ok=True)
                    import uuid
                    meta.replace(history/(str(uuid.uuid4())+'.json'))
                if key is None:
                    url=os.environ.get('DICTA_API_URL') or input('API URL from POST section: ').strip()
                    u=urlsplit(url)
                    if u.scheme!='https' or not u.hostname or not u.hostname.endswith('.dicta.org.il') or u.username or u.password or u.query or u.fragment:raise ValueError('Invalid Dicta URL')
                    key=os.environ.get('DICTA_API_KEY') or getpass.getpass('Personal API key (hidden): ')
                    if not key.strip():raise ValueError('Empty key')
                print(wid,ch['file'],'waiting 20 seconds before request...',flush=True);time.sleep(20)
                save(meta,dict(input_sha256=ch['sha256'],parameters=PARAMS,started=time.time()))
                req=urllib.request.Request(url,data=json.dumps(dict(PARAMS,data=s,apiKey=key),ensure_ascii=False).encode(),headers={'Content-Type':'text/plain;charset=UTF-8'},method='POST')
                class NoRedirect(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self,*args,**kwargs):return None
                try:
                    with urllib.request.build_opener(NoRedirect).open(req,timeout=180) as r:raw=r.read()
                except Exception as exc:
                    import socket,ssl
                    reason=getattr(exc,'reason',exc)
                    if isinstance(exc,urllib.error.HTTPError):
                        diagnostic='HTTP '+str(exc.code)
                        hints={401:'Check API key.',403:'Access denied; check API permission/key.',429:'Rate limited; wait before recovery.',500:'Server error.',502:'Gateway error.',503:'Service unavailable.',504:'Gateway timeout.'}
                        hint=hints.get(exc.code,'HTTP request rejected; share this status code.')
                    elif isinstance(reason,ssl.SSLError):diagnostic='TLS_CERTIFICATE_OR_HANDSHAKE';hint='Check system clock and certificate/proxy setup; TLS verification remains enabled.'
                    elif isinstance(reason,(TimeoutError,socket.timeout)):diagnostic='TIMEOUT';hint='Server completion is unknown; recovery may repeat this request.'
                    elif isinstance(reason,socket.gaierror):diagnostic='DNS_LOOKUP_FAILED';hint='Check Internet/DNS connection.'
                    else:diagnostic=type(reason).__name__;hint='Connection failed; share this error category.'
                    record=json.loads(meta.read_text(encoding='utf-8'));record['failure']={'category':diagnostic,'hint':hint,'time':time.time()};save(meta,record)
                    raise RuntimeError(diagnostic+'. '+hint+' State retained; no automatic retry.') from None
                tmp=dest/'response.part';tmp.write_bytes(raw);tmp.replace(response)
                saved=json.loads(meta.read_text(encoding='utf-8'));saved['response_sha256']=sha(raw);save(meta,saved)
            raw=response.read_bytes();record=json.loads(meta.read_text(encoding='utf-8'))
            if record['input_sha256']!=ch['sha256'] or record['parameters']!=PARAMS or record.get('response_sha256')!=sha(raw):raise ValueError('Cached response provenance mismatch')
            text,report=audit(s,json.loads(raw));report.update(work_id=wid,chunk=ch['file'],input_sha256=ch['sha256'],response_sha256=sha(raw),parameters=PARAMS)
            (dest/'candidate.txt').write_text(text,encoding='utf-8',newline='\n');save(dest/'review.json',report)
            summary.append(dict(work_id=wid,chunk=ch['file'],folder=str(dest.relative_to(base)),letter_changes=len(report['letter_changes']),flags=len(report['review_flags'])))
            save(out/'summary.json',dict(status='ACQUISITION_IN_PROGRESS',chunks=summary))
            print(wid,ch['file'],'saved; review required',flush=True)
        save(out/'summary.json',dict(status='ACQUISITION_COMPLETE_REVIEW_REQUIRED',chunks=summary))
    finally:
        lock.unlink()

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STOP:',str(e) if isinstance(e,(ValueError,RuntimeError,FileExistsError)) else type(e).__name__)
        raise SystemExit(1)
