"""One-chunk Dicta pilot. No credentials or service URL are distributed."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import time
import unicodedata
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PARAMS = dict(task='nakdan', useTokenization=True, genre='modern',
              addmorph=True, matchpartial=True, keepmetagim=True, keepqq=True)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def letters(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if '\u05d0' <= c <= '\u05ea')

def render(source, response):
    tokens = response['data']
    if not isinstance(tokens, list) or ''.join(t['str'] for t in tokens) != source:
        raise ValueError('Response tokens do not reconstruct exact input')
    output, changes = [], []
    for i, t in enumerate(tokens):
        if type(t.get('sep')) is not bool:
            raise ValueError('Invalid separator flag')
        if t['sep']:
            output.append(t['str'])
            continue
        options = t['nakdan']['options']
        if not options or not isinstance(options[0].get('w'), str):
            raise ValueError('Missing vocalized candidate')
        w = options[0]['w'].replace('|', '')
        if letters(w) != letters(t['str']):
            changes.append(dict(token=i, source=t['str'], candidate=w))
        output.append(w)
    return ''.join(output), changes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--send', action='store_true', help='Send one chunk if no cached response exists')
    args = ap.parse_args()
    base = ROOT / 'data/data_processed/modern/benyehuda'
    folder = base / 'nakdan_batches/523'
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    ch = manifest['chunks'][0]
    if ch['file'] != '0001.txt':
        raise ValueError('Unexpected pilot filename')
    data = (folder / ch['file']).read_bytes()
    if sha(data) != ch['sha256']:
        raise ValueError('Input hash mismatch')
    source = data.decode('utf-8')
    if not source or len(source.encode('utf-16-le')) // 2 > 30000:
        raise ValueError('Invalid input length')
    fingerprint = sha(data + json.dumps(PARAMS, sort_keys=True).encode())[:16]
    out = base / 'nakdan_pilot' / fingerprint
    cached = out / 'response.json'
    if not cached.exists():
        if not args.send:
            print('OFFLINE INPUT VERIFIED. No API request made. Use run\\dicta_control_pilot.bat to send one chunk.')
            return
        url = os.environ.get('DICTA_API_URL') or input('API URL from Dicta instructions (POST section): ').strip()
        from urllib.parse import urlsplit
        u = urlsplit(url)
        if u.scheme != 'https' or not u.hostname or not u.hostname.endswith('.dicta.org.il') or u.username or u.password or u.query or u.fragment:
            raise ValueError('Expected HTTPS Dicta service URL without credentials/query')
        key = os.environ.get('DICTA_API_KEY') or getpass.getpass('Personal API key (hidden): ')
        if not key.strip():
            raise ValueError('Empty API key')
        out.mkdir(parents=True, exist_ok=True)
        # Exclusive marker blocks concurrent requests and uncertain automatic retries.
        marker = out / 'request_started.json'
        with marker.open('x', encoding='utf-8') as f:
            json.dump(dict(started=time.time(), input_sha256=sha(data), parameters=PARAMS), f)
        body = json.dumps(dict(PARAMS, data=source, apiKey=key), ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'text/plain;charset=UTF-8'}, method='POST')
        # Do not follow redirects carrying a personal key to another endpoint.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **kw):
                return None
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=180) as r:
                raw = r.read()
        except Exception:
            raise RuntimeError('Request failed; no automatic retry. Request marker retained. Do not send logs containing credentials.') from None
        temp = out / 'response.part'
        temp.write_bytes(raw)
        temp.replace(cached)
    raw = cached.read_bytes()
    result, changes = render(source, json.loads(raw))
    (out / 'candidate.txt').write_text(result, encoding='utf-8', newline='\n')
    report = dict(work_id='523', chunk=ch['file'], input_sha256=sha(data),
                  response_sha256=sha(raw), parameters=PARAMS, exact_input_reconstruction=True,
                  letter_changes=changes, status='REVIEW_REQUIRED',
                  note='Automatic vocalization; not approved for phonetic analysis. Meteg marks carriers here.')
    (out / 'review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('Pilot saved:', out)
    print('Changed Hebrew-letter tokens:', len(changes), '; vocalization requires manual review.')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('STOP:', str(e) if isinstance(e, (ValueError, RuntimeError, FileExistsError)) else type(e).__name__)
        raise SystemExit(1)
