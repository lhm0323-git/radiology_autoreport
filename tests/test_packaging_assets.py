import unittest
from pathlib import Path

import config_manager
from packaging_assets import validate_packaging_inputs


class TestPackagingAssets(unittest.TestCase):
    def test_unified_runtime_assets_and_config_are_packaging_ready(self):
        base_dir = Path(__file__).resolve().parents[1]
        result = validate_packaging_inputs(base_dir, config_manager.default_config())

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["missing_spec_tokens"], [])


if __name__ == "__main__":
    unittest.main()
