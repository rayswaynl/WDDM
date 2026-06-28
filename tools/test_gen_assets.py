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

if __name__ == '__main__':
    unittest.main()
