import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QMessageBox

import setup_wizard


class TestSetupWizardConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ris_roi_calibration_updates_alt_o_scan_roi(self):
        config = {"auto_detect": {"monitor_idx": 3, "roi": {"left_pct": 0.0}}}
        saved = {}
        roi = {"left_pct": 0.1, "top_pct": 0.2, "width_pct": 0.3, "height_pct": 0.4}

        with patch.object(setup_wizard, "get_monitor_info", return_value={"left": 0, "top": 0, "width": 100, "height": 100}):
            with patch.object(setup_wizard, "_confirm_ready", return_value=True):
                with patch.object(setup_wizard, "_run_region_step", return_value=roi):
                    with patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok):
                        result = setup_wizard.run_patient_id_calibration(config, lambda data: saved.update(data))

        self.assertTrue(result)
        self.assertEqual(saved["roi_patient_id"], roi)
        self.assertEqual(saved["auto_detect"]["roi"], roi)

    def test_paste_calibration_saves_focus_point(self):
        config = {"click_before_paste": {"monitor_idx": 3}}
        saved = {}
        point = {"x_pct": 0.75, "y_pct": 0.5}

        with patch.object(setup_wizard, "get_monitor_info", return_value={"left": 0, "top": 0, "width": 100, "height": 100}):
            with patch.object(setup_wizard, "_confirm_ready", return_value=True):
                with patch.object(setup_wizard, "_run_click_step", return_value=point):
                    with patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok):
                        result = setup_wizard.run_paste_calibration(config, lambda data: saved.update(data))

        self.assertTrue(result)
        self.assertEqual(
            saved["click_before_paste"],
            {"enabled": True, "monitor_idx": 3, "x_pct": 0.75, "y_pct": 0.5},
        )

    def test_bone_age_calibration_saves_hand_roi(self):
        config = {"monitors": {"bone_age": 2}}
        saved = {}
        roi = {"left_pct": 0.05, "top_pct": 0.08, "width_pct": 0.82, "height_pct": 0.74}

        with patch.object(setup_wizard, "get_monitor_info", return_value={"left": 0, "top": 0, "width": 100, "height": 100}):
            with patch.object(setup_wizard, "_confirm_ready", return_value=True):
                with patch.object(setup_wizard, "_run_region_step", return_value=roi):
                    with patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok):
                        result = setup_wizard.run_bone_age_calibration(config, lambda data: saved.update(data))

        self.assertTrue(result)
        self.assertEqual(saved["roi_bone_age"], roi)


if __name__ == "__main__":
    unittest.main()
