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

if __name__ == '__main__':
    unittest.main()
