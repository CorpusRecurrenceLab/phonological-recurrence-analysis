"""Acquire/verify comparison texts: bundled public-domain Bialik, restricted Rivlin."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, urllib.request
from html.parser import HTMLParser
from pathlib import Path

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / "src" / "analysis"))
from spatial import words_to_segments


class ActualTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.parts = []
        self.found = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        parent = self.stack[-1] if self.stack else (False, False)
        active = parent[0] or attr.get("id") == "actualtext"
        skip = parent[1] or tag in {"script", "style", "sup"} or "footnotes" in attr.get("class", "").split() or attr.get("role") == "doc-endnotes"
        if attr.get("id") == "actualtext":
            self.found += 1
        if tag not in {"br", "hr", "img", "input", "meta", "link", "wbr", "source"}:
            self.stack.append((active, skip))
        if active and not skip and tag in {"p", "br", "blockquote", "div", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag not in {"br", "hr", "img", "input", "meta", "link", "wbr", "source"} and self.stack:
            active, skip = self.stack.pop()
            if active and not skip and tag in {"p", "blockquote", "div"}:
                self.parts.append("\n")

    def handle_data(self, data):
        if self.stack and self.stack[-1][0] and not self.stack[-1][1]:
            self.parts.append(data)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 reproducibility-research/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def verify_rivlin_html(raw: bytes, expected_sha256: str) -> str:
    parser = ActualTextParser()
    parser.feed(raw.decode("utf-8"))
    if parser.found != 1:
        raise ValueError("Expected exactly one actualtext element for Rivlin")
    text = re.sub(r"\n\s*\n+", "\n\n", "".join(parser.parts)).strip() + "\n"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Rivlin text does not match the pinned extracted-text SHA-256")
    return text


def available_rivlin_path(cache_path: Path) -> Path | None:
    explicit = os.environ.get("HASHIRA_RIVLIN_HTML")
    if explicit:
        supplied = Path(explicit).expanduser()
        if not supplied.is_file():
            raise FileNotFoundError(f"HASHIRA_RIVLIN_HTML is not a file: {supplied}")
        return supplied
    return cache_path if cache_path.is_file() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Check a locally provided Rivlin HTML without network access")
    ap.add_argument("--offline", action="store_true", help="Do not fetch missing source files")
    args = ap.parse_args()
    config = {row["corpus"]: row for row in json.loads((P / "config" / "additional_sources.json").read_text(encoding="utf-8"))}
    dest = P / ".local" / "additional"
    if not args.check:
        dest.mkdir(parents=True, exist_ok=True)
    segments = {}
    metadata = []
    bundled_bialik = P / "sources" / "original" / "modern" / "bialik_beir_haharegah.txt"
    for corpus, ident in (("rivlin_ali_baba", "17705"), ("bialik_beir_haharegah", "1784")):
        expected = config[corpus]
        url = expected["url"]
        html_path = dest / f"{corpus}.html"
        if corpus == "bialik_beir_haharegah":
            text = bundled_bialik.read_text(encoding="utf-8")
            raw = bundled_bialik.read_bytes()
            removed = expected["removed"]
            input_type = "bundled_public_domain_extracted_text"
        else:
            source_path = available_rivlin_path(html_path)
            if source_path is None:
                if args.check or args.offline or os.environ.get("HASHIRA_OFFLINE") == "1":
                    raise RuntimeError(
                        "Rivlin source unavailable. Supply the authorized Project Ben-Yehuda "
                        "HTML using HASHIRA_RIVLIN_HTML (absolute path) or place it at "
                        f"{html_path}. This file is intentionally excluded from Git."
                    )
                try:
                    raw_fetched = fetch(url)
                    # Do not cache a changed/unverified download.
                    verify_rivlin_html(raw_fetched, expected["text_sha256"])
                    html_path.write_bytes(raw_fetched)
                except Exception as exc:
                    raise RuntimeError(
                        "Could not retrieve Rivlin's permission-only translation. "
                        "Obtain its HTML from the cited Project Ben-Yehuda page using "
                        "an authorized route; set HASHIRA_RIVLIN_HTML to its path. "
                        "HTTPS certificate validation is never disabled."
                    ) from exc
                source_path = html_path
            raw = source_path.read_bytes()
            text = verify_rivlin_html(raw, expected["text_sha256"])
            if args.check:
                print(f"PASS restricted Rivlin source: {source_path} (verified extracted-text SHA-256)")
                return
            removed = []
            input_type = "provider_html"

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest != expected["text_sha256"]:
            raise ValueError(f"Extracted source text changed: {corpus}")
        text_path = dest / f"{corpus}.txt"
        text_path.write_text(text, encoding="utf-8", newline="\n")
        segments[corpus] = words_to_segments(text, [0, len(text)])
        metadata.append({
            "corpus": corpus,
            "url": url,
            "input_sha256": hashlib.sha256(raw).hexdigest(),
            "input_type": input_type,
            "text_sha256": digest,
            "removed": removed,
            "characters": len(text),
            "segments": len(segments[corpus]),
        })
    (dest / "segments_words.json").write_text(json.dumps(segments, ensure_ascii=False), encoding="utf-8", newline="\n")
    (dest / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("PASS additional source acquisition and text-hash verification")


if __name__ == "__main__":
    main()
