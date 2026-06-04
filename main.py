import sys
import threading
import queue
import time
import ctypes
import os
import subprocess
from ctypes.wintypes import MSG

from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QSystemTrayIcon, QMenu, QTextEdit, QVBoxLayout
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QTextCursor
from PyQt6.QtCore import QTimer, QAbstractNativeEventFilter, Qt, QObject, pyqtSignal

class WinHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callbacks):
        super().__init__()
        self.callbacks = callbacks

    def nativeEventFilter(self, eventType, message):
        try:
            if eventType == b"windows_generic_MSG" or eventType == b"windows_dispatcher_MSG":
                msg = MSG.from_address(int(message))
                if msg.message == 0x0312: # WM_HOTKEY
                    if msg.wParam in self.callbacks:
                        self.callbacks[msg.wParam]()
                        return True, 0
        except Exception:
            pass
        return False, 0


class LogBridge(QObject):
    line_logged = pyqtSignal()


class LazyBoneAgeAI:
    def __init__(self):
        self._engine = None
        self._lock = threading.RLock()

    def predict(self, image, is_female):
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    print("Initializing Bone Age AI Engine on first Bone Age use...")
                    from ai_engine import BoneAgeAIEngine
                    self._engine = BoneAgeAIEngine()
        return self._engine.predict(image, is_female)

from config_manager import load_config, save_config
from ocr_engine import OCREngine
from modules import BoneAgeModule, DexaModule, ModuleContext
from platform_routing import build_hotkey_task_map, parse_hotkey, route_dexa_from_ris_lines
from single_instance import acquire_single_instance

class AppManager:
    def create_text_icon(self, text, bg_color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(bg_color))
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.config = load_config()
        
        # System Tray setup
        self.icon_da = self.create_text_icon("RAD", "#008CBA")
        self.icon_ds = self.create_text_icon("DS", "#808080")
        
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon_da)
        self.tray.setToolTip("Radiology Auto-Reporter")
        
        menu = QMenu()
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self.open_settings)

        calibration_menu = menu.addMenu("ROI Calibration")
        calibration_menu.addAction("Full ROI Setup Wizard").triggered.connect(self.run_setup_wizard)
        calibration_menu.addAction("RIS OCR ROI").triggered.connect(self.run_ris_roi_calibration)
        calibration_menu.addAction("BMD ROI").triggered.connect(self.run_bmd_roi_calibration)
        calibration_menu.addAction("Whole Body ROI").triggered.connect(self.run_wb_roi_calibration)
        calibration_menu.addAction("Calcium ROI").triggered.connect(self.run_calcium_roi_calibration)
        calibration_menu.addAction("Bone Age Hand ROI").triggered.connect(self.run_bone_age_roi_calibration)
        calibration_menu.addAction("RIS Paste Focus").triggered.connect(self.run_paste_focus_calibration)
        menu.addSeparator()
        
        self.suspend_action = menu.addAction("Suspend / Active")
        self.suspend_action.setCheckable(True)
        self.suspend_action.setChecked(False)
        self.suspend_action.triggered.connect(self.toggle_suspend)
        
        reload_action = menu.addAction("Reload Config")
        reload_action.triggered.connect(self.reload_config)
        log_action = menu.addAction("Show Session Log")
        log_action.triggered.connect(self.show_session_log)
        menu.addSeparator()
        
        quit_action = menu.addAction("Quit Auto-Reporter")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray.setContextMenu(menu)
        self.tray.show()
        
        self.is_suspended = False
        self.modules = {}
        self.log_messages = []
        self.log_window = None
        self.log_bridge = LogBridge()
        self.log_bridge.line_logged.connect(self.refresh_log_window)
        
        # Bind hotkeys
        self.hk_dexa_scan = self.config.get("hotkeys", {}).get("start_scan", "alt+o")
        self.hk_dexa_toggle = self.config.get("hotkeys", {}).get("toggle_bmd", "shift+2")
        self.hk_ba_m = self.config.get("hotkeys", {}).get("force_male", "shift+b")
        self.hk_ba_f = self.config.get("hotkeys", {}).get("force_female", "shift+g")
        self.hk_suspend = self.config.get("hotkeys", {}).get("suspend", "scroll_lock")
        
        # Worker Queue setup
        self.q = queue.Queue()
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Native Hotkey setup
        self.hotkey_callbacks = {}
        self.hotkey_filter = WinHotkeyFilter(self.hotkey_callbacks)
        self.app.installNativeEventFilter(self.hotkey_filter)
        
        self.hotkeys_registered = False
        self.suspend_hotkey_registered = False
        self.register_suspend_hotkey()
        
        self.log_event("Radiology Auto-Reporter running.")
        self.tray.showMessage("Auto-Reporter Started", "Ready.")
        
        # Start Active Window Polling Timer
        self.active_win_timer = QTimer()
        self.active_win_timer.timeout.connect(self.check_active_window)
        self.active_win_timer.start(500)

    def unregister_all_hotkeys(self):
        ctypes.windll.user32.UnregisterHotKey(None, 1)
        ctypes.windll.user32.UnregisterHotKey(None, 2)
        ctypes.windll.user32.UnregisterHotKey(None, 3)
        ctypes.windll.user32.UnregisterHotKey(None, 4)
        for hotkey_id in (1, 2, 3, 4):
            self.hotkey_callbacks.pop(hotkey_id, None)
        self.hotkeys_registered = False

    def register_suspend_hotkey(self):
        ctypes.windll.user32.UnregisterHotKey(None, 99)
        self.hotkey_callbacks.pop(99, None)
        self.suspend_hotkey_registered = False
        self.register_hotkey(99, self.hk_suspend, lambda: self.toggle_suspend(not self.is_suspended))
        self.suspend_hotkey_registered = 99 in self.hotkey_callbacks

    def unregister_suspend_hotkey(self):
        ctypes.windll.user32.UnregisterHotKey(None, 99)
        self.hotkey_callbacks.pop(99, None)
        self.suspend_hotkey_registered = False

    def log_event(self, message):
        line = f"[{time.strftime('%H:%M:%S')}] {message}"
        self.log_messages.append(line)
        self.log_messages = self.log_messages[-500:]
        print(line)
        self.log_bridge.line_logged.emit()

    def refresh_log_window(self):
        if self.log_window is None:
            return
        editor = self.log_window.findChild(QTextEdit, "session_log_text")
        if editor is not None:
            editor.setPlainText("\n".join(self.log_messages))
            editor.moveCursor(QTextCursor.MoveOperation.End)

    def show_session_log(self):
        if self.log_window is None:
            dlg = QDialog()
            dlg.setWindowTitle("Radiology Auto-Reporter Session Log")
            dlg.resize(800, 500)
            layout = QVBoxLayout(dlg)
            editor = QTextEdit()
            editor.setObjectName("session_log_text")
            editor.setReadOnly(True)
            layout.addWidget(editor)
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dlg.hide)
            layout.addWidget(close_btn)
            self.log_window = dlg

        editor = self.log_window.findChild(QTextEdit, "session_log_text")
        if editor is not None:
            editor.setPlainText("\n".join(self.log_messages))
            editor.moveCursor(QTextCursor.MoveOperation.End)
        self.log_window.show()

    def check_active_window(self):
        if self.is_suspended:
            return
            
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd: return
            
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.lower()
            
            is_target = False
            target_keywords = self.config.get("hotkeys", {}).get("active_window_keywords", ["報告", "ris", "pacs", "屏基", "病患", "impax"])
            for kw in target_keywords:
                if kw in title:
                    is_target = True
                    break
                    
            if is_target and not self.hotkeys_registered:
                task_map = build_hotkey_task_map(self.config)
                self.register_hotkey(1, self.hk_dexa_scan, lambda: self.q.put(task_map[1]))
                self.register_hotkey(2, self.hk_dexa_toggle, lambda: self.q.put(task_map[2]))
                self.register_hotkey(3, self.hk_ba_m, lambda: self.q.put(task_map[3]))
                self.register_hotkey(4, self.hk_ba_f, lambda: self.q.put(task_map[4]))
                self.hotkeys_registered = True
                self.log_event(f"RIS Window Detected ({title}). Hotkeys Enabled.")
                
            elif not is_target and self.hotkeys_registered:
                self.unregister_all_hotkeys()
                self.log_event(f"Switched to {title}. Hotkeys Disabled.")
        except Exception:
            pass
            
    def open_settings(self):
        from settings_ui import SettingsDialog
        dlg = SettingsDialog(self.config, "config.json")
        if dlg.exec():
            self.reload_config()

    def _run_calibration(self, calibration_fn):
        was_suspended = self.is_suspended
        if not was_suspended:
            self.toggle_suspend(True)
        try:
            completed = calibration_fn(self.config, save_config)
            self.reload_config()
            return completed
        finally:
            if not was_suspended:
                self.toggle_suspend(False)

    def run_setup_wizard(self):
        from setup_wizard import run_setup_wizard
        self._run_calibration(run_setup_wizard)

    def run_ris_roi_calibration(self):
        from setup_wizard import run_patient_id_calibration
        self._run_calibration(run_patient_id_calibration)

    def run_bmd_roi_calibration(self):
        from setup_wizard import run_bmd_calibration
        self._run_calibration(run_bmd_calibration)

    def run_wb_roi_calibration(self):
        from setup_wizard import run_wb_calibration
        self._run_calibration(run_wb_calibration)

    def run_calcium_roi_calibration(self):
        from setup_wizard import run_calcium_calibration
        self._run_calibration(run_calcium_calibration)

    def run_bone_age_roi_calibration(self):
        from setup_wizard import run_bone_age_calibration
        self._run_calibration(run_bone_age_calibration)

    def run_paste_focus_calibration(self):
        from setup_wizard import run_paste_calibration
        self._run_calibration(run_paste_calibration)
            
    def toggle_suspend(self, checked):
        self.is_suspended = checked
        if checked:
            self.tray.setIcon(self.icon_ds)
            self.tray.showMessage("Reporter Suspended", "Auto-detect and hotkeys are paused.", QSystemTrayIcon.MessageIcon.Warning, 2000)
            if self.hotkeys_registered:
                self.unregister_all_hotkeys()
        else:
            self.tray.setIcon(self.icon_da)
            self.tray.showMessage("Reporter Active", "Resuming operations.", QSystemTrayIcon.MessageIcon.Information, 2000)
            self.check_active_window()
            
    def reload_config(self):
        self.config = load_config()
        self.hk_dexa_scan = self.config.get("hotkeys", {}).get("start_scan", "alt+o")
        self.hk_dexa_toggle = self.config.get("hotkeys", {}).get("toggle_bmd", "shift+2")
        self.hk_ba_m = self.config.get("hotkeys", {}).get("force_male", "shift+b")
        self.hk_ba_f = self.config.get("hotkeys", {}).get("force_female", "shift+g")
        self.hk_suspend = self.config.get("hotkeys", {}).get("suspend", "scroll_lock")
        self.register_suspend_hotkey()
        
        if self.hotkeys_registered and not self.is_suspended:
            task_map = build_hotkey_task_map(self.config)
            self.unregister_all_hotkeys()
            self.register_hotkey(1, self.hk_dexa_scan, lambda: self.q.put(task_map[1]))
            self.register_hotkey(2, self.hk_dexa_toggle, lambda: self.q.put(task_map[2]))
            self.register_hotkey(3, self.hk_ba_m, lambda: self.q.put(task_map[3]))
            self.register_hotkey(4, self.hk_ba_f, lambda: self.q.put(task_map[4]))
            self.hotkeys_registered = True
            
        self.tray.showMessage("Config Reloaded", "Settings updated successfully.")

    def register_hotkey(self, hotkey_id, hotkey_str, callback):
        try:
            modifiers, vk = parse_hotkey(hotkey_str)
        except ValueError as exc:
            print(exc)
            return
        
        res = ctypes.windll.user32.RegisterHotKey(None, hotkey_id, modifiers, vk)
        if res:
            self.hotkey_callbacks[hotkey_id] = callback
        else:
            print(f"Failed to register native hotkey: {hotkey_str}")

    def worker_loop(self):
        self.ocr = OCREngine(self.config)
        if self.config.get("ocr_performance", {}).get("warm_up_on_start", True):
            threading.Thread(target=self.ocr.warm_up, daemon=True).start()
        self.bone_age_ai = LazyBoneAgeAI()
        dexa_module = DexaModule()
        self.modules = {
            "dexa": dexa_module,
            "dexa_wb": dexa_module,
            "dexa_bmd": dexa_module,
            "dexa_calcium": dexa_module,
            "dexa_toggle": dexa_module,
            "bone_age": BoneAgeModule(self.bone_age_ai),
        }
        self.log_event("Engines Initialized.")
        
        last_signature = ""
        import mss
        import cv2
        import numpy as np
        
        while True:
            try:
                cfg = self.config.get("auto_detect", {})
                poll_interval = cfg.get("poll_interval_seconds", 5.0)
                
                # Format: (task_type, param)
                task_data = self.q.get(timeout=poll_interval)
                if task_data[0] == "dexa_scan_ris":
                    self.scan_ris_and_dispatch()
                else:
                    self.process_screen(task_data[0], task_data[1])
                self.q.task_done()
                
            except queue.Empty:
                if self.is_suspended or not cfg.get("enabled", False):
                    continue
                    
                try:
                    monitor_idx = cfg.get("monitor_idx", 3)
                    roi = cfg.get("roi", {"left_pct": 0.0, "top_pct": 0.0, "width_pct": 1.0, "height_pct": 0.5})
                    
                    with mss.mss() as sct:
                        if monitor_idx < len(sct.monitors):
                            m = sct.monitors[monitor_idx]
                            box = {
                                "left": int(m["left"] + m["width"] * roi["left_pct"]),
                                "top": int(m["top"] + m["height"] * roi["top_pct"]),
                                "width": int(m["width"] * roi["width_pct"]),
                                "height": int(m["height"] * roi["height_pct"])
                            }
                            img = np.array(sct.grab(box))
                            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                            
                            res = self.ocr.extract_text(img)
                            if not res: 
                                continue
                            
                            signature_parts = []
                            for item in res:
                                if len(item) > 1 and isinstance(item[1], str):
                                    txt = item[1].lower()
                                    if "病歷號" in txt or "姓名" in txt or "年齡" in txt:
                                        signature_parts.append(txt)
                                    if "文字報告" in txt or "whole body" in txt or "bmd" in txt or "骨質密度" in txt:
                                        signature_parts.append(txt)
                                    if "bone age" in txt or "boneage" in txt:
                                        signature_parts.append(txt)
                                    if "radiographic" in txt or "atlas" in txt or "skeletal" in txt:
                                        signature_parts.append(txt)
                                    
                            signature = " ".join(signature_parts)
                            
                            if signature and signature != last_signature:
                                is_wb = "whole body" in signature or "脂肪分析" in signature
                                is_bmd = "bmd" in signature or "骨質密度" in signature
                                
                                has_ai = "radiographic" in signature or "atlas" in signature or "skeletal" in signature
                                is_bone_age = ("bone age" in signature or "boneage" in signature) and not has_ai
                                
                                has_ai_last = "radiographic" in last_signature or "atlas" in last_signature or "skeletal" in last_signature
                                was_bone_age = ("bone age" in last_signature or "boneage" in last_signature) and not has_ai_last
                                
                                last_signature = signature
                                
                                import winsound
                                delay = cfg.get("delay_after_detect", 2.0)
                                
                                if is_wb:
                                    print(f"Auto-detected DEXA Whole Body: {signature}")
                                    winsound.Beep(1500, 150)
                                    time.sleep(delay)
                                    winsound.Beep(2000, 200)
                                    m_idx = self.config.get("monitors", {}).get("dexa_wb", 1)
                                    self.q.put(('dexa', {"mode": "whole_body", "monitor_idx": m_idx, "is_manual": False}))
                                elif is_bmd:
                                    print(f"Auto-detected DEXA BMD: {signature}")
                                    winsound.Beep(1500, 150)
                                    time.sleep(delay)
                                    winsound.Beep(2000, 200)
                                    m_idx = self.config.get("monitors", {}).get("dexa_bmd", 2)
                                    self.q.put(('dexa', {"mode": "bmd", "monitor_idx": m_idx, "is_manual": False}))
                                elif is_bone_age and not was_bone_age:
                                    print(f"Auto-detected Bone Age: {signature}")
                                    winsound.Beep(1500, 150)
                                    time.sleep(delay)
                                    winsound.Beep(2000, 200)
                                    print("Use shift+b for male or shift+g for female.")
                                    
                except Exception as e:
                    print(f"Auto Detect Error: {e}")
            except Exception as e:
                print(f"Worker Loop Error: {e}")

    def scan_ris_and_dispatch(self):
        import mss
        import cv2
        import numpy as np

        cfg = self.config.get("auto_detect", {})
        monitor_idx = cfg.get("monitor_idx", 3)
        roi = cfg.get("roi")
        if not roi:
            self.log_event("[Scan RIS] Error: ROI missing in config.")
            return

        with mss.mss() as sct:
            if monitor_idx >= len(sct.monitors):
                self.log_event("[Scan RIS] Error: monitor index invalid in config.")
                return

            mon = sct.monitors[monitor_idx]
            box = {
                "left": int(mon["left"] + mon["width"] * roi.get("left_pct", 0.0)),
                "top": int(mon["top"] + mon["height"] * roi.get("top_pct", 0.0)),
                "width": int(mon["width"] * roi.get("width_pct", 1.0)),
                "height": int(mon["height"] * roi.get("height_pct", 0.5)),
            }
            self.log_event(f"[Scan RIS] Capturing RIS Screen on Monitor {monitor_idx}")
            img = np.array(sct.grab(box))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            cv2.imwrite("ris_roi_debug.png", img)
            self.log_event(f"[Scan RIS] Saved RIS ROI debug image: ris_roi_debug.png ({img.shape[1]}x{img.shape[0]})")

        t_start = time.time()
        res = self.extract_ris_text(img)
        used_fallback = False
        if not res and cfg.get("ris_fallback_enabled", False):
            fallback_roi = {"left_pct": 0.0, "top_pct": 0.0, "width_pct": 1.0, "height_pct": 0.5}
            with mss.mss() as sct:
                if monitor_idx < len(sct.monitors):
                    mon = sct.monitors[monitor_idx]
                    fallback_box = {
                        "left": int(mon["left"] + mon["width"] * fallback_roi["left_pct"]),
                        "top": int(mon["top"] + mon["height"] * fallback_roi["top_pct"]),
                        "width": int(mon["width"] * fallback_roi["width_pct"]),
                        "height": int(mon["height"] * fallback_roi["height_pct"]),
                    }
                    fallback_img = np.array(sct.grab(fallback_box))
                    fallback_img = cv2.cvtColor(fallback_img, cv2.COLOR_BGRA2BGR)
                    cv2.imwrite("ris_roi_fallback_debug.png", fallback_img)
                    self.log_event(
                        "[Scan RIS] Configured ROI OCR empty; trying fallback RIS ROI: "
                        f"ris_roi_fallback_debug.png ({fallback_img.shape[1]}x{fallback_img.shape[0]})"
                    )
                    res = self.extract_ris_text(fallback_img)
                    used_fallback = bool(res)
        self.log_event(f"[Timing] RIS OCR took {time.time() - t_start:.2f}s")
        if not res:
            self.log_event("[Scan RIS] Error: No text found in RIS ROI.")
            return
        if used_fallback:
            self.log_event("[Scan RIS] Fallback RIS ROI produced OCR text; recalibrate RIS OCR ROI if this repeats.")

        ris_lines = [item[1] for item in res if len(item) > 1 and isinstance(item[1], str)]
        routed = route_dexa_from_ris_lines(ris_lines, self.config)
        if not routed:
            self.log_event("[Scan RIS] Mode could not be determined from RIS text.")
            return

        self.log_event(f"[Scan RIS] Dispatching task: {routed}")
        self.process_screen(routed[0], routed[1])

    def extract_ris_text(self, image):
        import cv2

        res = self.ocr.extract_text(image)
        if res:
            return res

        h, w = image.shape[:2]
        tile_specs = [
            ("right_half", image[:, w // 2:]),
            ("right_third", image[:, int(w * 0.62):]),
            ("right_quarter", image[:, int(w * 0.70):]),
        ]
        for tile_name, tile in tile_specs:
            res = self.ocr.extract_text(tile)
            if res:
                cv2.imwrite(f"ris_roi_{tile_name}_debug.png", tile)
                self.log_event(f"[Scan RIS] OCR succeeded on precise ROI tile: {tile_name}.")
                return res
            if tile.shape[0] < 220:
                enlarged = cv2.resize(tile, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                res = self.ocr.extract_text(enlarged)
                if res:
                    cv2.imwrite(f"ris_roi_{tile_name}_debug.png", tile)
                    self.log_event(f"[Scan RIS] OCR succeeded on 2x precise ROI tile: {tile_name}.")
                    return res

        if h < 260 or w < 1800:
            scale = 3.0 if h < 150 else 2.0
            padded = cv2.copyMakeBorder(
                image,
                max(16, h // 3),
                max(16, h // 3),
                max(12, w // 80),
                max(12, w // 80),
                cv2.BORDER_CONSTANT,
                value=(255, 255, 255),
            )
            enlarged = cv2.resize(padded, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            sharp = cv2.addWeighted(enlarged, 1.5, cv2.GaussianBlur(enlarged, (0, 0), 1.2), -0.5, 0)
            variants = [enlarged, sharp]
            gray = cv2.cvtColor(sharp, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            variants.append(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR))

            for variant in variants:
                res = self.ocr.extract_text(variant)
                if res:
                    self.log_event(f"[Scan RIS] OCR succeeded after {scale:g}x ROI upscale/padding.")
                    return res
            cv2.imwrite("ris_roi_upscaled_debug.png", variants[-1])
            self.log_event(
                "RIS ROI OCR remained empty after upscale/padding. "
                "Saved ris_roi_upscaled_debug.png for inspection."
            )
        return []

    def process_screen(self, task_type, param):
        try:
            time.sleep(0.3)
            self.log_event(f"Processing Task: {task_type} (Param: {param})")
            module = self.modules.get(task_type)
            if not module:
                self.log_event(f"Unknown task type: {task_type}")
                return

            from output import paste_to_ris

            context = ModuleContext(
                config=self.config,
                ocr=self.ocr,
                paste=paste_to_ris,
                notify=self.log_event,
            )
            result = module.run(task_type, param, context)
            for action in result.actions:
                if action.get("type") == "open_reference_pdf":
                    self.open_bone_age_pdf(action.get("page", 1))
            if result.module_id == "dexa":
                self.log_event("DEXA Done!")
            if result.module_id == "bone_age":
                self.log_event("Bone Age Done!")
            
        except Exception as e:
            self.log_event(f"Error processing: {e}")

    def open_bone_age_pdf(self, target_page):
        pdf_path = self.config.get("bone_age_atlas_path", r"D:\download\Atlas_of_Hand_Bone_Age.pdf")
        pdf_viewer = self.config.get("bone_age_viewer_path", r"D:\programs\PDF-XChange Viewer_2.5.311\PDFXCview.exe")

        if not os.path.exists(pdf_path):
            self.log_event(f"Atlas PDF not found at {pdf_path}")
            return

        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible

        target_hwnd = None
        def foreach_window(hwnd, lParam):
            nonlocal target_hwnd
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buf, length + 1)
                    title = buf.value
                    if "PDF-XChange Viewer" in title or "Atlas_of_Hand_Bone_Age.pdf" in title:
                        target_hwnd = hwnd
                        return False
            return True

        EnumWindows(EnumWindowsProc(foreach_window), 0)

        if target_hwnd:
            import pyautogui

            self.log_event(f"PDF Viewer open (HWND: {target_hwnd}). Jumping to page {target_page}")
            ctypes.windll.user32.ShowWindow(target_hwnd, 5)
            ctypes.windll.user32.SetForegroundWindow(target_hwnd)
            time.sleep(0.3)

            pyautogui.hotkey('ctrl', 'shift', 'n')
            time.sleep(0.4)

            import pyperclip
            pyperclip.copy(str(target_page))
            pyautogui.hotkey('ctrl', 'v')

            time.sleep(0.3)
            pyautogui.press('enter')
        else:
            self.log_event(f"PDF Viewer not open. Launching directly to page {target_page}")
            if os.path.exists(pdf_viewer):
                cmd = [pdf_viewer, "/A", f"page={target_page}", pdf_path]
                try:
                    subprocess.Popen(cmd)
                except Exception as e:
                    self.log_event(f"Failed to open PDF-XChange Viewer: {e}")
                    os.startfile(pdf_path)
            else:
                os.startfile(pdf_path)
        
    def quit_app(self):
        self.unregister_all_hotkeys()
        self.unregister_suspend_hotkey()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

def main():
    instance_guard = acquire_single_instance()
    if instance_guard.already_running:
        print("Radiology Auto-Reporter is already running. Exiting duplicate instance.")
        return 0

    try:
        manager = AppManager()
        manager.run()
    finally:
        instance_guard.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
