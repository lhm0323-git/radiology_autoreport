from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QGroupBox,
                             QMessageBox, QCheckBox, QDoubleSpinBox, QSpinBox, QTabWidget, QWidget,
                             QTextEdit)
from PyQt6.QtCore import Qt
import config_manager

class SettingsDialog(QDialog):
    def __init__(self, config, config_file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Radiology Auto-Reporter Settings")
        self.resize(600, 500)
        
        self.config = config
        self.config_file_path = config_file_path
        
        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- TAB 1: General & Auto-Detect ---
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        ad_group = QGroupBox("Auto-Detect Settings")
        ad_layout = QFormLayout()
        
        self.ad_enabled_cb = QCheckBox("Enable Background Polling")
        self.ad_enabled_cb.setChecked(self.config.get("auto_detect", {}).get("enabled", False))
        
        self.ad_poll_sb = QDoubleSpinBox()
        self.ad_poll_sb.setRange(1.0, 60.0)
        self.ad_poll_sb.setValue(self.config.get("auto_detect", {}).get("poll_interval_seconds", 5.0))
        
        self.ad_delay_sb = QDoubleSpinBox()
        self.ad_delay_sb.setRange(0.5, 10.0)
        self.ad_delay_sb.setValue(self.config.get("auto_detect", {}).get("delay_after_detect", 2.0))
        
        self.ad_monitor_sb = QSpinBox()
        self.ad_monitor_sb.setRange(0, 5)
        self.ad_monitor_sb.setValue(self.config.get("auto_detect", {}).get("monitor_idx", 3))
        
        ad_layout.addRow("", self.ad_enabled_cb)
        ad_layout.addRow("Polling Interval (sec):", self.ad_poll_sb)
        ad_layout.addRow("Delay Before Capture (sec):", self.ad_delay_sb)
        ad_layout.addRow("RIS Monitor Index:", self.ad_monitor_sb)
        ad_group.setLayout(ad_layout)
        general_layout.addWidget(ad_group)

        platform_group = QGroupBox("Platform Hotkeys")
        platform_layout = QFormLayout()
        self.hk_suspend_edit = QLineEdit(self.config.get("hotkeys", {}).get("suspend", "scroll_lock"))
        platform_layout.addRow("Suspend / Resume:", self.hk_suspend_edit)
        platform_group.setLayout(platform_layout)
        general_layout.addWidget(platform_group)

        focus_group = QGroupBox("Paste Focus")
        focus_layout = QFormLayout()
        focus_cfg = self.config.get("click_before_paste", {})
        self.focus_enabled_cb = QCheckBox("Click before paste")
        self.focus_enabled_cb.setChecked(focus_cfg.get("enabled", True))

        self.focus_monitor_sb = QSpinBox()
        self.focus_monitor_sb.setRange(0, 5)
        self.focus_monitor_sb.setValue(focus_cfg.get("monitor_idx", 3))

        self.focus_x_sb = QDoubleSpinBox()
        self.focus_x_sb.setRange(0.0, 1.0)
        self.focus_x_sb.setSingleStep(0.001)
        self.focus_x_sb.setDecimals(4)
        self.focus_x_sb.setValue(focus_cfg.get("x_pct", 0.7547))

        self.focus_y_sb = QDoubleSpinBox()
        self.focus_y_sb.setRange(0.0, 1.0)
        self.focus_y_sb.setSingleStep(0.001)
        self.focus_y_sb.setDecimals(4)
        self.focus_y_sb.setValue(focus_cfg.get("y_pct", 0.4981))

        focus_layout.addRow("", self.focus_enabled_cb)
        focus_layout.addRow("RIS Monitor Index:", self.focus_monitor_sb)
        focus_layout.addRow("Report X %:", self.focus_x_sb)
        focus_layout.addRow("Report Y %:", self.focus_y_sb)
        focus_group.setLayout(focus_layout)
        general_layout.addWidget(focus_group)

        general_layout.addStretch()
        self.tabs.addTab(general_tab, "General")
        
        # --- TAB 2: DEXA Settings ---
        dexa_tab = QWidget()
        dexa_layout = QVBoxLayout(dexa_tab)
        
        hk_group_dexa = QGroupBox("DEXA Hotkeys")
        hk_layout_dexa = QFormLayout()
        self.hk_dexa_scan_edit = QLineEdit(self.config.get("hotkeys", {}).get("start_scan", "alt+o"))
        self.hk_bmd_toggle_edit = QLineEdit(self.config.get("hotkeys", {}).get("toggle_bmd", "shift+2"))
        hk_layout_dexa.addRow("RIS Scan Trigger:", self.hk_dexa_scan_edit)
        hk_layout_dexa.addRow("BMD T/Z Toggle:", self.hk_bmd_toggle_edit)
        
        mon_cfg = self.config.get("monitors", {"dexa_wb": 1, "dexa_bmd": 2, "dexa_calcium": 2, "bone_age": 2})
        self.mon_wb_sb = QSpinBox()
        self.mon_wb_sb.setRange(0, 5)
        self.mon_wb_sb.setValue(mon_cfg.get("dexa_wb", 1))
        
        self.mon_bmd_sb = QSpinBox()
        self.mon_bmd_sb.setRange(0, 5)
        self.mon_bmd_sb.setValue(mon_cfg.get("dexa_bmd", 2))

        self.mon_calcium_sb = QSpinBox()
        self.mon_calcium_sb.setRange(0, 5)
        self.mon_calcium_sb.setValue(mon_cfg.get("dexa_calcium", mon_cfg.get("dexa_bmd", 2)))
        
        hk_layout_dexa.addRow("Whole Body Monitor:", self.mon_wb_sb)
        hk_layout_dexa.addRow("BMD Monitor:", self.mon_bmd_sb)
        hk_layout_dexa.addRow("Calcium Monitor:", self.mon_calcium_sb)
        
        hk_group_dexa.setLayout(hk_layout_dexa)
        dexa_layout.addWidget(hk_group_dexa)
        
        dexa_layout.addStretch()
        self.tabs.addTab(dexa_tab, "DEXA")

        # --- TAB 3: Report Templates ---
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)

        self.whole_body_template_edit = QTextEdit()
        self.whole_body_template_edit.setPlainText(self.config.get("whole_body_template", ""))
        template_layout.addWidget(QLabel("Whole Body Template"))
        template_layout.addWidget(self.whole_body_template_edit)

        self.bmd_template_edit = QTextEdit()
        self.bmd_template_edit.setPlainText(self.config.get("bmd_template", ""))
        template_layout.addWidget(QLabel("BMD Template"))
        template_layout.addWidget(self.bmd_template_edit)

        self.calcium_template_edit = QTextEdit()
        self.calcium_template_edit.setPlainText(self.config.get("calcium_template", ""))
        template_layout.addWidget(QLabel("Calcium Template"))
        template_layout.addWidget(self.calcium_template_edit)

        self.bone_age_template_edit = QTextEdit()
        self.bone_age_template_edit.setPlainText(self.config.get("bone_age_template", ""))
        template_layout.addWidget(QLabel("Bone Age Template"))
        template_layout.addWidget(self.bone_age_template_edit)

        self.tabs.addTab(template_tab, "Templates")
        
        # --- TAB 4: Bone Age Settings ---
        ba_tab = QWidget()
        ba_layout = QVBoxLayout(ba_tab)
        
        roi_note = QLabel(
            "Bone Age hand ROI is calibrated from the tray menu: "
            "ROI Calibration > Bone Age Hand ROI."
        )
        roi_note.setWordWrap(True)
        ba_layout.addWidget(roi_note)

        calibration_group = QGroupBox("Bone Age Calibration")
        calibration_layout = QFormLayout()
        self.ba_bias_offset = QDoubleSpinBox()
        self.ba_bias_offset.setRange(-60.0, 60.0)
        self.ba_bias_offset.setSingleStep(1.0)
        self.ba_bias_offset.setDecimals(1)
        self.ba_bias_offset.setValue(self.config.get("bone_age_bias_offset_months", -5.0))
        calibration_layout.addRow("Bias Offset (months):", self.ba_bias_offset)
        calibration_group.setLayout(calibration_layout)
        ba_layout.addWidget(calibration_group)
        
        hk_group_ba = QGroupBox("Bone Age Hotkeys")
        hk_layout_ba = QFormLayout()
        self.hk_ba_m_edit = QLineEdit(self.config.get("hotkeys", {}).get("force_male", "shift+b"))
        self.hk_ba_f_edit = QLineEdit(self.config.get("hotkeys", {}).get("force_female", "shift+g"))
        hk_layout_ba.addRow("Force Male Trigger:", self.hk_ba_m_edit)
        hk_layout_ba.addRow("Force Female Trigger:", self.hk_ba_f_edit)
        
        mon_cfg = self.config.get("monitors", {"dexa_wb": 1, "dexa_bmd": 2, "bone_age": 2})
        self.mon_ba_sb = QSpinBox()
        self.mon_ba_sb.setRange(0, 5)
        self.mon_ba_sb.setValue(mon_cfg.get("bone_age", 2))
        hk_layout_ba.addRow("PACS Monitor Index:", self.mon_ba_sb)
        
        hk_group_ba.setLayout(hk_layout_ba)
        ba_layout.addWidget(hk_group_ba)
        
        pdf_group = QGroupBox("PDF Atlas Paths")
        pdf_layout = QFormLayout()
        self.pdf_path_edit = QLineEdit(self.config.get("bone_age_atlas_path", ""))
        self.viewer_path_edit = QLineEdit(self.config.get("bone_age_viewer_path", ""))
        pdf_layout.addRow("Atlas PDF Path:", self.pdf_path_edit)
        pdf_layout.addRow("PDF Viewer Path:", self.viewer_path_edit)
        pdf_group.setLayout(pdf_layout)
        ba_layout.addWidget(pdf_group)
        
        ba_layout.addStretch()
        self.tabs.addTab(ba_tab, "Bone Age")
        
        # --- BUTTONS ---
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(btn_layout)

    def save_settings(self):
        # General
        if "auto_detect" not in self.config:
            self.config["auto_detect"] = {}
            
        self.config["auto_detect"]["enabled"] = self.ad_enabled_cb.isChecked()
        self.config["auto_detect"]["poll_interval_seconds"] = self.ad_poll_sb.value()
        self.config["auto_detect"]["delay_after_detect"] = self.ad_delay_sb.value()
        self.config["auto_detect"]["monitor_idx"] = self.ad_monitor_sb.value()

        if "click_before_paste" not in self.config:
            self.config["click_before_paste"] = {}
        self.config["click_before_paste"]["enabled"] = self.focus_enabled_cb.isChecked()
        self.config["click_before_paste"]["monitor_idx"] = self.focus_monitor_sb.value()
        self.config["click_before_paste"]["x_pct"] = self.focus_x_sb.value()
        self.config["click_before_paste"]["y_pct"] = self.focus_y_sb.value()
        
        # Hotkeys
        if "hotkeys" not in self.config:
            self.config["hotkeys"] = {}
        self.config["hotkeys"].pop("dexa_wb", None)
        self.config["hotkeys"].pop("dexa_bmd", None)
        self.config["hotkeys"]["start_scan"] = self.hk_dexa_scan_edit.text().strip()
        self.config["hotkeys"]["toggle_bmd"] = self.hk_bmd_toggle_edit.text().strip()
        self.config["hotkeys"]["suspend"] = self.hk_suspend_edit.text().strip()
        self.config["hotkeys"].pop("bone_age", None)
        self.config["hotkeys"].pop("bone_age_trigger", None)
        self.config["hotkeys"]["force_male"] = self.hk_ba_m_edit.text().strip()
        self.config["hotkeys"]["force_female"] = self.hk_ba_f_edit.text().strip()

        # Templates
        self.config["whole_body_template"] = self.whole_body_template_edit.toPlainText()
        self.config["bmd_template"] = self.bmd_template_edit.toPlainText()
        self.config["calcium_template"] = self.calcium_template_edit.toPlainText()
        self.config["bone_age_template"] = self.bone_age_template_edit.toPlainText()
        self.config.setdefault("templates", {})
        self.config["templates"]["whole_body"] = self.config["whole_body_template"]
        self.config["templates"]["bmd"] = self.config["bmd_template"]
        self.config["templates"]["calcium"] = self.config["calcium_template"]
        
        # Bone Age PDF
        self.config["bone_age_atlas_path"] = self.pdf_path_edit.text().strip()
        self.config["bone_age_viewer_path"] = self.viewer_path_edit.text().strip()
        
        self.config["bone_age_bias_offset_months"] = self.ba_bias_offset.value()
        
        # Monitors
        if "monitors" not in self.config:
            self.config["monitors"] = {}
        self.config["monitors"]["dexa_wb"] = self.mon_wb_sb.value()
        self.config["monitors"]["dexa_bmd"] = self.mon_bmd_sb.value()
        self.config["monitors"]["dexa_calcium"] = self.mon_calcium_sb.value()
        self.config["monitors"]["bone_age"] = self.mon_ba_sb.value()
        
        config_manager.save_config(self.config)
        self.accept()
