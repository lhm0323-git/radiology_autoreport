import unittest
from pathlib import Path

import config_manager
import preflight_check


class TestPreflightCheck(unittest.TestCase):
    def test_warns_for_missing_external_cache_when_not_strict(self):
        config = config_manager.default_config()
        base = Path(__file__).resolve().parents[1]

        result = preflight_check.run_preflight(base, config, strict_external=False, env={})

        self.assertTrue(result.ok, result)
        self.assertTrue(any("local HuggingFace cache missing" in item for item in result.warnings))

    def test_strict_external_requires_hf_cache_and_external_paths(self):
        config = config_manager.default_config()
        config["bone_age_atlas_path"] = r"Z:\missing\atlas.pdf"
        config["bone_age_viewer_path"] = r"Z:\missing\PDFXCview.exe"
        base = Path(__file__).resolve().parents[1]

        result = preflight_check.run_preflight(base, config, strict_external=True, env={})

        self.assertFalse(result.ok)
        self.assertTrue(any("bone_age_atlas_path not found" in item for item in result.missing))
        self.assertTrue(any("bone_age_viewer_path not found" in item for item in result.missing))
        self.assertTrue(any("local HuggingFace cache missing" in item for item in result.missing))


if __name__ == "__main__":
    unittest.main()
