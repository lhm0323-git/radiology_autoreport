import mss
from PyQt6.QtCore import QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class RegionSelector(QWidget):
    region_selected = pyqtSignal(dict)

    def __init__(self, monitor_info, title, instruction, color="#FF4444", parent=None):
        super().__init__(parent)
        self.monitor_info = monitor_info
        self.title = title
        self.instruction = instruction
        self.color = QColor(color)
        self.drag_start = None
        self.current_rect = None
        self.confirmed = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setGeometry(
            monitor_info["left"],
            monitor_info["top"],
            monitor_info["width"],
            monitor_info["height"],
        )
        self.setWindowOpacity(0.92)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if self.current_rect and self.current_rect.width() > 5 and self.current_rect.height() > 5:
            painter.setPen(QPen(self.color, 3, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(self.color.red(), self.color.green(), self.color.blue(), 30))
            painter.drawRect(self.current_rect)

            w_pct = self.current_rect.width() / self.width() * 100
            h_pct = self.current_rect.height() / self.height() * 100
            label = f"{self.current_rect.width()} x {self.current_rect.height()} px ({w_pct:.1f}% x {h_pct:.1f}%)"
            painter.fillRect(QRect(self.current_rect.x(), self.current_rect.y() - 28, 360, 24), QColor(0, 0, 0, 180))
            painter.setPen(QPen(QColor("white")))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(self.current_rect.x() + 5, self.current_rect.y() - 10, label)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillRect(QRect(0, 0, self.width(), 96), QColor(0, 0, 0, 220))
        painter.setPen(QPen(self.color))
        painter.setFont(QFont("Microsoft JhengHei", 22, QFont.Weight.Bold))
        painter.drawText(20, 44, self.title)
        painter.setPen(QPen(QColor("white")))
        painter.setFont(QFont("Microsoft JhengHei", 15))
        painter.drawText(20, 78, self.instruction)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillRect(QRect(0, self.height() - 42, self.width(), 42), QColor(0, 0, 0, 220))
        painter.setPen(QPen(QColor("#DDDDDD")))
        painter.setFont(QFont("Microsoft JhengHei", 11))
        painter.drawText(20, self.height() - 15, "Drag to select ROI. Enter = save, R = redo, Esc = cancel.")
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = event.pos()
            self.current_rect = QRect(event.pos(), event.pos())
            self.update()

    def mouseMoveEvent(self, event):
        if self.drag_start:
            x1 = min(self.drag_start.x(), event.pos().x())
            y1 = min(self.drag_start.y(), event.pos().y())
            x2 = max(self.drag_start.x(), event.pos().x())
            y2 = max(self.drag_start.y(), event.pos().y())
            self.current_rect = QRect(x1, y1, x2 - x1, y2 - y1)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouseMoveEvent(event)
            self.drag_start = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.current_rect and self.current_rect.width() > 10 and self.current_rect.height() > 10:
                result = {
                    "left_pct": round(self.current_rect.x() / self.width(), 4),
                    "top_pct": round(self.current_rect.y() / self.height(), 4),
                    "width_pct": round(self.current_rect.width() / self.width(), 4),
                    "height_pct": round(self.current_rect.height() / self.height(), 4),
                }
                self.confirmed = True
                self.region_selected.emit(result)
                self.close()
        elif event.key() == Qt.Key.Key_R:
            self.drag_start = None
            self.current_rect = None
            self.update()


class ClickSelector(QWidget):
    point_selected = pyqtSignal(dict)

    def __init__(self, monitor_info, title, instruction, color="#42A5F5", parent=None):
        super().__init__(parent)
        self.monitor_info = monitor_info
        self.title = title
        self.instruction = instruction
        self.color = QColor(color)
        self.click_pos = None
        self.confirmed = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setGeometry(
            monitor_info["left"],
            monitor_info["top"],
            monitor_info["width"],
            monitor_info["height"],
        )
        self.setWindowOpacity(0.92)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if self.click_pos:
            painter.setPen(QPen(self.color, 3))
            painter.drawLine(self.click_pos.x() - 25, self.click_pos.y(), self.click_pos.x() + 25, self.click_pos.y())
            painter.drawLine(self.click_pos.x(), self.click_pos.y() - 25, self.click_pos.x(), self.click_pos.y() + 25)
            painter.drawEllipse(self.click_pos, 18, 18)
            label = f"({self.click_pos.x() / self.width() * 100:.1f}%, {self.click_pos.y() / self.height() * 100:.1f}%)"
            painter.fillRect(QRect(self.click_pos.x() + 25, self.click_pos.y() - 20, 170, 24), QColor(0, 0, 0, 180))
            painter.setPen(QPen(QColor("white")))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(self.click_pos.x() + 30, self.click_pos.y() - 2, label)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillRect(QRect(0, 0, self.width(), 80), QColor(0, 0, 0, 220))
        painter.setPen(QPen(self.color))
        painter.setFont(QFont("Microsoft JhengHei", 18, QFont.Weight.Bold))
        painter.drawText(20, 34, self.title)
        painter.setPen(QPen(QColor("white")))
        painter.setFont(QFont("Microsoft JhengHei", 12))
        painter.drawText(20, 62, self.instruction)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillRect(QRect(0, self.height() - 42, self.width(), 42), QColor(0, 0, 0, 220))
        painter.setPen(QPen(QColor("#DDDDDD")))
        painter.setFont(QFont("Microsoft JhengHei", 11))
        painter.drawText(20, self.height() - 15, "Click target point. Enter = save, Esc = cancel.")
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_pos = event.pos()
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.click_pos:
            result = {
                "x_pct": round(self.click_pos.x() / self.width(), 4),
                "y_pct": round(self.click_pos.y() / self.height(), 4),
            }
            self.confirmed = True
            self.point_selected.emit(result)
            self.close()


class ScreenSelectionDialog(QDialog):
    def __init__(self, num_monitors, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Radiology ROI Setup")
        self.setMinimumWidth(460)
        self.result = None

        monitors = config.get("monitors", {})
        ris_default = config.get("auto_detect", {}).get("monitor_idx", 3)

        layout = QVBoxLayout(self)
        header = QLabel("Select monitors for RIS, DEXA, and Bone Age capture.")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(header)
        layout.addWidget(QLabel(f"Detected monitors: 1 to {num_monitors - 1}"))

        form_group = QGroupBox("Monitor Mapping")
        form_layout = QFormLayout()
        self.ris_sb = _monitor_spinbox(num_monitors, ris_default)
        self.bmd_sb = _monitor_spinbox(num_monitors, monitors.get("dexa_bmd", 2))
        self.wb_sb = _monitor_spinbox(num_monitors, monitors.get("dexa_wb", 1))
        self.calcium_sb = _monitor_spinbox(num_monitors, monitors.get("dexa_calcium", monitors.get("dexa_bmd", 2)))
        self.bone_age_sb = _monitor_spinbox(num_monitors, monitors.get("bone_age", 2))
        form_layout.addRow("RIS monitor:", self.ris_sb)
        form_layout.addRow("BMD monitor:", self.bmd_sb)
        form_layout.addRow("Whole Body monitor:", self.wb_sb)
        form_layout.addRow("Calcium monitor:", self.calcium_sb)
        form_layout.addRow("Bone Age monitor:", self.bone_age_sb)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        next_btn = QPushButton("Continue")
        cancel_btn.clicked.connect(self.reject)
        next_btn.clicked.connect(self.accept_settings)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(next_btn)
        layout.addLayout(buttons)

    def accept_settings(self):
        self.result = {
            "ris_monitor": self.ris_sb.value(),
            "bmd_monitor": self.bmd_sb.value(),
            "wb_monitor": self.wb_sb.value(),
            "calcium_monitor": self.calcium_sb.value(),
            "bone_age_monitor": self.bone_age_sb.value(),
        }
        self.accept()


def _monitor_spinbox(num_monitors, value):
    sb = QSpinBox()
    sb.setRange(1, max(1, num_monitors - 1))
    sb.setValue(min(max(1, int(value)), max(1, num_monitors - 1)))
    return sb


def get_monitor_info(monitor_idx):
    with mss.mss() as sct:
        if 1 <= monitor_idx < len(sct.monitors):
            mon = sct.monitors[monitor_idx]
            return {
                "left": mon["left"],
                "top": mon["top"],
                "width": mon["width"],
                "height": mon["height"],
            }
    return None


def _run_region_step(monitor_info, title, instruction, color):
    result_holder = [None]
    selector = RegionSelector(monitor_info, title, instruction, color)
    selector.region_selected.connect(lambda data: result_holder.__setitem__(0, data))
    selector.show()
    selector.activateWindow()
    selector.raise_()
    while selector.isVisible():
        QApplication.processEvents()
    if not selector.confirmed:
        return None
    return result_holder[0]


def _run_click_step(monitor_info, title, instruction, color):
    result_holder = [None]
    selector = ClickSelector(monitor_info, title, instruction, color)
    selector.point_selected.connect(lambda data: result_holder.__setitem__(0, data))
    selector.show()
    selector.activateWindow()
    selector.raise_()
    while selector.isVisible():
        QApplication.processEvents()
    if not selector.confirmed:
        return None
    return result_holder[0]


def _calibrate_exam(monitor_info, exam_name, color_patient, color_results, start_step=1, total_steps=2):
    patient = _run_region_step(
        monitor_info,
        f"Step {start_step}/{total_steps}: {exam_name} patient info",
        f"Drag the {exam_name} patient demographics area, then press Enter.",
        color_patient,
    )
    if patient is None:
        return None

    results = _run_region_step(
        monitor_info,
        f"Step {start_step + 1}/{total_steps}: {exam_name} results",
        f"Drag the {exam_name} numeric results table area, then press Enter.",
        color_results,
    )
    if results is None:
        return None
    return patient, results


def run_bmd_calibration(config, save_callback):
    mon_idx = config.get("monitors", {}).get("dexa_bmd", 2)
    mon = get_monitor_info(mon_idx)
    if not mon:
        QMessageBox.warning(None, "Monitor unavailable", f"Monitor {mon_idx} is not available.")
        return False
    if not _confirm_ready("BMD ROI", f"Open the BMD PACS screen on monitor {mon_idx}."):
        return False
    result = _calibrate_exam(mon, "BMD", "#FF6B6B", "#FF4444")
    if result is None:
        return False
    config["roi_bmd"] = {"patient_info": result[0], "results": result[1]}
    save_callback(config)
    QMessageBox.information(None, "BMD ROI Saved", "BMD patient and results ROIs have been saved.")
    return True


def run_wb_calibration(config, save_callback):
    mon_idx = config.get("monitors", {}).get("dexa_wb", 1)
    mon = get_monitor_info(mon_idx)
    if not mon:
        QMessageBox.warning(None, "Monitor unavailable", f"Monitor {mon_idx} is not available.")
        return False
    if not _confirm_ready("Whole Body ROI", f"Open the Whole Body PACS screen on monitor {mon_idx}."):
        return False
    result = _calibrate_exam(mon, "Whole Body", "#66BB6A", "#43A047")
    if result is None:
        return False
    config["roi_wb"] = {"patient_info": result[0], "results": result[1]}
    save_callback(config)
    QMessageBox.information(None, "Whole Body ROI Saved", "Whole Body patient and results ROIs have been saved.")
    return True


def run_calcium_calibration(config, save_callback):
    monitors = config.get("monitors", {})
    mon_idx = monitors.get("dexa_calcium", monitors.get("dexa_bmd", 2))
    mon = get_monitor_info(mon_idx)
    if not mon:
        QMessageBox.warning(None, "Monitor unavailable", f"Monitor {mon_idx} is not available.")
        return False
    if not _confirm_ready("Calcium ROI", f"Open the Calcium table PACS screen on monitor {mon_idx}."):
        return False
    result = _calibrate_exam(mon, "Calcium", "#29B6F6", "#0288D1")
    if result is None:
        return False
    config.setdefault("monitors", {})["dexa_calcium"] = mon_idx
    config["roi_calcium"] = {"patient_info": result[0], "results": result[1]}
    save_callback(config)
    QMessageBox.information(None, "Calcium ROI Saved", "Calcium patient and results ROIs have been saved.")
    return True


def run_bone_age_calibration(config, save_callback):
    mon_idx = config.get("monitors", {}).get("bone_age", 2)
    mon = get_monitor_info(mon_idx)
    if not mon:
        QMessageBox.warning(None, "Monitor unavailable", f"Monitor {mon_idx} is not available.")
        return False
    if not _confirm_ready(
        "Bone Age Hand ROI",
        (
            f"Open the Bone Age hand image on PACS monitor {mon_idx}.\n\n"
            "Suggested ROI:\n"
            "- Include the full left hand, wrist, and distal radius/ulna.\n"
            "- Leave about 3-5% margin around the anatomy.\n"
            "- Exclude PACS toolbar, patient text, image frame, and black borders."
        ),
    ):
        return False
    result = _run_region_step(
        mon,
        "Bone Age hand ROI",
        "Drag around the hand/wrist anatomy only, then press Enter.",
        "#AB47BC",
    )
    if result is None:
        return False
    config["roi_bone_age"] = result
    save_callback(config)
    QMessageBox.information(
        None,
        "Bone Age ROI Saved",
        "Bone Age hand ROI has been saved. Restart or Reload Config before testing.",
    )
    return True


def run_patient_id_calibration(config, save_callback):
    mon_idx = config.get("auto_detect", {}).get("monitor_idx", 3)
    mon = get_monitor_info(mon_idx)
    if not mon:
        QMessageBox.warning(None, "Monitor unavailable", f"Monitor {mon_idx} is not available.")
        return False
    if not _confirm_ready("RIS ROI", f"Open the RIS window on monitor {mon_idx}."):
        return False
    result = _run_region_step(
        mon,
        "RIS order/OCR ROI",
        "Drag the RIS order text area used by Alt+O, then press Enter.",
        "#FFEB3B",
    )
    if result is None:
        return False
    config["roi_patient_id"] = result
    config.setdefault("auto_detect", {})["roi"] = result
    save_callback(config)
    QMessageBox.information(None, "RIS ROI Saved", "RIS order/OCR ROI has been saved.")
    return True


def run_paste_calibration(config, save_callback):
    mon_idx = config.get("click_before_paste", {}).get("monitor_idx", config.get("auto_detect", {}).get("monitor_idx", 3))
    mon = get_monitor_info(mon_idx)
    if not mon:
        QMessageBox.warning(None, "Monitor unavailable", f"Monitor {mon_idx} is not available.")
        return False
    if not _confirm_ready("Paste Focus", f"Open RIS on monitor {mon_idx}."):
        return False
    result = _run_click_step(
        mon,
        "RIS paste focus point",
        "Click inside the RIS report text field, then press Enter.",
        "#42A5F5",
    )
    if result is None:
        return False
    config["click_before_paste"] = {
        "enabled": True,
        "monitor_idx": mon_idx,
        "x_pct": result["x_pct"],
        "y_pct": result["y_pct"],
    }
    save_callback(config)
    QMessageBox.information(None, "Paste Focus Saved", "RIS paste focus point has been saved.")
    return True


def run_setup_wizard(config, save_callback):
    with mss.mss() as sct:
        num_monitors = len(sct.monitors)
    if num_monitors < 2:
        QMessageBox.warning(None, "No monitor", "No capture monitor is available.")
        return False

    dlg = ScreenSelectionDialog(num_monitors, config)
    if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.result:
        return False

    screens = dlg.result
    config.setdefault("monitors", {})
    config["monitors"]["dexa_wb"] = screens["wb_monitor"]
    config["monitors"]["dexa_bmd"] = screens["bmd_monitor"]
    config["monitors"]["dexa_calcium"] = screens["calcium_monitor"]
    config["monitors"]["bone_age"] = screens["bone_age_monitor"]
    config.setdefault("auto_detect", {})["monitor_idx"] = screens["ris_monitor"]
    save_callback(config)

    steps = [
        ("RIS order/OCR ROI", run_patient_id_calibration),
        ("BMD ROI", run_bmd_calibration),
        ("Whole Body ROI", run_wb_calibration),
        ("Calcium ROI", run_calcium_calibration),
        ("Bone Age hand ROI", run_bone_age_calibration),
        ("RIS paste focus point", run_paste_calibration),
    ]
    for label, fn in steps:
        if not _confirm_ready(label, f"Continue with {label} calibration?"):
            continue
        fn(config, save_callback)

    config["setup_completed"] = True
    save_callback(config)
    QMessageBox.information(None, "Setup Saved", "ROI setup is complete. Use Reload Config if the app is already running.")
    return True


def _confirm_ready(title, text):
    reply = QMessageBox.information(
        None,
        title,
        f"{text}\n\nDrag/select carefully on the target monitor. Press Enter to save, Esc to cancel.",
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
    )
    return reply != QMessageBox.StandardButton.Cancel
