import unittest
import gen_assets

CFG = '''class CfgVehicles
{
\tclass All
\t{
\t\tscope = 0;
\t\tdisplayName = "Unknown";
\t};
\tclass Land_HBarrier_large : NonStrategic
\t{
\t\tscope = 2;
\t\tdisplayName = "HBarrier (large)";
\t};
\tclass ForwardOnly;
\tclass M2StaticMG : StaticMGWeapon
\t{
\t\tdisplayName = "M2 .50 cal";
\t};
};'''

class TestParse(unittest.TestCase):
    def test_names_and_displaynames(self):
        out = gen_assets.parse_cfg_classes(CFG)
        self.assertIn('Land_HBarrier_large', out)
        self.assertEqual(out['Land_HBarrier_large'], 'HBarrier (large)')
        self.assertEqual(out['M2StaticMG'], 'M2 .50 cal')

    def test_forward_declaration_recorded_empty(self):
        out = gen_assets.parse_cfg_classes(CFG)
        self.assertIn('ForwardOnly', out)
        self.assertEqual(out['ForwardOnly'], '')

    def test_nested_class_captured(self):
        out = gen_assets.parse_cfg_classes(CFG)
        self.assertIn('All', out)
        self.assertEqual(out['All'], 'Unknown')

HTML = """
const CATALOG=[
  {grp:'Walls', cls:'Land_HBarrier_large', size:[2.5,0.6], style:'hbarrier'},
  {grp:'MG / GL', cls:'M2StaticMG', size:[1,1.4], style:'mg', cat:'mg'},
];
const PRESETS={ demo:{ name:'x', tpl:'T', objs:[ ['Hedgehog',[0,0,0],0], ['Land_HBarrier_large',[2,0,0],0] ] } };
"""

class TestExtract(unittest.TestCase):
    def test_extracts_catalog_and_preset_classnames(self):
        out = gen_assets.extract_classnames(HTML)
        self.assertEqual(out, {'Land_HBarrier_large', 'M2StaticMG', 'Hedgehog'})

import tempfile, os
from pathlib import Path as _P

class TestImages(unittest.TestCase):
    def test_index_and_copy(self):
        with tempfile.TemporaryDirectory() as d:
            ref = _P(d) / 'Images' / 'A2' / 'Objects' / 'Fortifications'
            ref.mkdir(parents=True)
            (ref / 'Land_HBarrier_large.jpg').write_bytes(b'JPGDATA')
            (ref / 'Hedgehog.jpg').write_bytes(b'JPGDATA')
            dest = _P(d) / 'out'
            idx = gen_assets.index_images(_P(d) / 'Images')
            copied, missing = gen_assets.copy_images(
                {'Land_HBarrier_large', 'Hedgehog', 'DoesNotExist'}, idx, dest)
            self.assertEqual(set(copied), {'Land_HBarrier_large', 'Hedgehog'})
            self.assertEqual(missing, ['DoesNotExist'])
            self.assertTrue((dest / 'Land_HBarrier_large.jpg').exists())

if __name__ == '__main__':
    unittest.main()
