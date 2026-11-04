from pathlib import Path
import json, sys, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'/'core'))
from phonetic_core_v2 import transliterate_word

class CoreSmoke(unittest.TestCase):
    def test_transcription_is_deterministic(self):
        a=transliterate_word('בְּרֵאשִׁית',return_units=True)
        b=transliterate_word('בְּרֵאשִׁית',return_units=True)
        self.assertEqual(a,b)
        self.assertTrue(a)
    def test_frozen_counts(self):
        d=json.loads((ROOT/'config'/'preparation_expected.json').read_text(encoding='utf-8'))
        self.assertEqual(d['counts']['source_books'],39)
        self.assertEqual(d['counts']['traditional_books'],24)
        self.assertEqual(d['counts']['words'],305584)
        self.assertEqual(d['counts']['sound_units'],1602109)

if __name__=='__main__': unittest.main()
