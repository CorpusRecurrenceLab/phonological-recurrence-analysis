"""Public-domain input and restriction guard tests."""
import hashlib, json, unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]
class SourceRightsTests(unittest.TestCase):
    def test_bialik_bundled_and_pinned(self):
        b=(P/'sources/original/modern/bialik_beir_haharegah.txt').read_bytes()
        cfg={x['corpus']: x for x in json.loads((P/'config/additional_sources.json').read_text(encoding='utf-8'))}
        self.assertEqual(hashlib.sha256(b).hexdigest(),cfg['bialik_beir_haharegah']['text_sha256'])
    def test_rivlin_not_bundled(self):
        self.assertFalse((P/'sources/original/modern/rivlin_ali_baba.txt').exists())
        self.assertFalse((P/'sources/original/modern/rivlin_ali_baba.html').exists())
