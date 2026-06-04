import unittest
from unittest.mock import mock_open, patch

import config_manager


class TestPlatformConfig(unittest.TestCase):
    def test_default_config_uses_manual_gender_bone_age_hotkeys(self):
        captured = {}

        def fake_dump(data, file_obj, **kwargs):
            captured.update(data)

        with patch.object(config_manager.os.path, "exists", return_value=False):
            with patch("builtins.open", mock_open()):
                with patch.object(config_manager.json, "dump", side_effect=fake_dump):
                    config = config_manager.load_config()

        self.assertNotIn("bone_age", config["hotkeys"])
        self.assertEqual(config["hotkeys"]["force_male"], "shift+b")
        self.assertEqual(config["hotkeys"]["force_female"], "shift+g")
        self.assertEqual(config["hotkeys"]["suspend"], "scroll_lock")
        self.assertFalse(config["auto_detect"]["enabled"])
        self.assertFalse(config["auto_detect"]["ris_fallback_enabled"])
        self.assertIn("roi_bmd", config)
        self.assertIn("roi_wb", config)
        self.assertIn("roi_calcium", config)
        self.assertTrue(config["click_before_paste"]["enabled"])
        self.assertEqual(config["click_before_paste"]["monitor_idx"], 3)
        self.assertEqual(config["bone_age_bias_offset_months"], -5.0)
        self.assertEqual(captured["bone_age_bias_offset_months"], -5.0)


if __name__ == "__main__":
    unittest.main()
