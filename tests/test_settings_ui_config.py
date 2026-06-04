import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

import config_manager
from settings_ui import SettingsDialog


class TestSettingsUiConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_settings_save_writes_unified_dexa_and_bone_age_config(self):
        config = config_manager.default_config()
        saved = {}

        dialog = SettingsDialog(config, "config.json")
        dialog.hk_dexa_scan_edit.setText("alt+o")
        dialog.hk_bmd_toggle_edit.setText("shift+2")
        dialog.hk_suspend_edit.setText("scroll_lock")
        dialog.hk_ba_m_edit.setText("shift+b")
        dialog.hk_ba_f_edit.setText("shift+g")
        dialog.mon_wb_sb.setValue(1)
        dialog.mon_bmd_sb.setValue(2)
        dialog.mon_calcium_sb.setValue(3)
        dialog.mon_ba_sb.setValue(2)
        dialog.ba_bias_offset.setValue(-5.0)
        dialog.focus_enabled_cb.setChecked(True)
        dialog.focus_monitor_sb.setValue(3)
        dialog.focus_x_sb.setValue(0.7547)
        dialog.focus_y_sb.setValue(0.4981)
        dialog.whole_body_template_edit.setPlainText("WB {fat_percent}\n\nVAT {vat_area}")
        dialog.bmd_template_edit.setPlainText("BMD {score_type} {score_value}")
        dialog.calcium_template_edit.setPlainText("Calcium total {Total}")
        dialog.bone_age_template_edit.setPlainText("Bone age {age_range}")

        with patch.object(config_manager, "save_config", side_effect=lambda data: saved.update(data)):
            dialog.save_settings()

        self.assertEqual(saved["hotkeys"]["start_scan"], "alt+o")
        self.assertEqual(saved["hotkeys"]["toggle_bmd"], "shift+2")
        self.assertEqual(saved["hotkeys"]["suspend"], "scroll_lock")
        self.assertEqual(saved["hotkeys"]["force_male"], "shift+b")
        self.assertEqual(saved["hotkeys"]["force_female"], "shift+g")
        self.assertNotIn("dexa_wb", saved["hotkeys"])
        self.assertNotIn("dexa_bmd", saved["hotkeys"])
        self.assertNotIn("bone_age", saved["hotkeys"])
        self.assertEqual(saved["monitors"]["dexa_wb"], 1)
        self.assertEqual(saved["monitors"]["dexa_bmd"], 2)
        self.assertEqual(saved["monitors"]["dexa_calcium"], 3)
        self.assertEqual(saved["monitors"]["bone_age"], 2)
        self.assertEqual(saved["bone_age_bias_offset_months"], -5.0)
        self.assertTrue(saved["click_before_paste"]["enabled"])
        self.assertEqual(saved["click_before_paste"]["monitor_idx"], 3)
        self.assertAlmostEqual(saved["click_before_paste"]["x_pct"], 0.7547, places=4)
        self.assertAlmostEqual(saved["click_before_paste"]["y_pct"], 0.4981, places=4)
        self.assertEqual(saved["whole_body_template"], "WB {fat_percent}\n\nVAT {vat_area}")
        self.assertEqual(saved["bmd_template"], "BMD {score_type} {score_value}")
        self.assertEqual(saved["calcium_template"], "Calcium total {Total}")
        self.assertEqual(saved["bone_age_template"], "Bone age {age_range}")
        self.assertEqual(saved["templates"]["whole_body"], saved["whole_body_template"])
        self.assertEqual(saved["templates"]["bmd"], saved["bmd_template"])
        self.assertEqual(saved["templates"]["calcium"], saved["calcium_template"])


if __name__ == "__main__":
    unittest.main()
