"""Acquire the two non-redistributed Project Ben-Yehuda comparison works."""
from __future__ import annotations
import hashlib, json, re, sys, urllib.request
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


def main():
    config = {row["corpus"]: row for row in json.loads((P / "config" / "additional_sources.json").read_text(encoding="utf-8"))}
    dest = P / ".local" / "additional"
    dest.mkdir(parents=True, exist_ok=True)
    segments = {}
    metadata = []
    for corpus, ident in (("rivlin_ali_baba", "17705"), ("bialik_beir_haharegah", "1784")):
        expected = config[corpus]
        url = expected["url"]
        html_path = dest / f"{corpus}.html"
        if not html_path.exists():
            html_path.write_bytes(fetch(url))
        raw = html_path.read_bytes()
        parser = ActualTextParser()
        parser.feed(raw.decode("utf-8"))
        if parser.found != 1:
            raise ValueError(f"Expected exactly one actualtext element for {corpus}")
        text = re.sub(r"\n\s*\n+", "\n\n", "".join(parser.parts)).strip() + "\n"
        removed = []
        if corpus == "bialik_beir_haharegah":
            colophon = 'תמוז–תשרי, תרס"ד.'
            if not text.rstrip().endswith(colophon):
                raise ValueError("Expected Bialik dated colophon not found")
            text = text.rstrip()[:-len(colophon)].rstrip() + "\n"
            removed.append({"kind": "dated_colophon", "text": colophon})
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest != expected["text_sha256"]:
            raise ValueError(f"Extracted source text changed: {corpus}")
        text_path = dest / f"{corpus}.txt"
        text_path.write_text(text, encoding="utf-8", newline="\n")
        segments[corpus] = words_to_segments(text, [0, len(text)])
        metadata.append({
            "corpus": corpus,
            "url": url,
            "download_sha256": hashlib.sha256(raw).hexdigest(),
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
