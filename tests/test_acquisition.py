"""Source adapter checks against real frozen verse projections."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('acquisition',ROOT/'src/download_sources.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class AcquisitionTests(unittest.TestCase):
    def test_source_content_checked_not_unrelated_metadata(self):
        frozen=json.loads((ROOT/'sources/variants/biblical/genesis_verses.json').read_text(encoding='utf-8'))
        chapters=[['']*n for n in frozen['chapter_lengths']]
        for v in frozen['verses']:chapters[v['chapter']-1][v['verse']-1]=v['source_text']
        response={'heVersionTitle':frozen['returned_version'],'he':chapters,'unrelated_service_metadata':'new value'}
        module.verify_biblical_response(response,frozen)
        response['he'][0][0]+=' altered'
        with self.assertRaises(ValueError):module.verify_biblical_response(response,frozen)
    def test_wrong_edition_rejected(self):
        with self.assertRaises(ValueError):module.verify_biblical_response({'heVersionTitle':'other'},{'returned_version':'required'})
