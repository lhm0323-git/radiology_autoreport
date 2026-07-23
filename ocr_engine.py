import threading


def bmd_warm_up_shapes(config, monitor_size):
    width, height = monitor_size
    roi_bmd = (config or {}).get("roi_bmd", {})
    shapes = []
    for key in ("patient_info", "results"):
        roi = roi_bmd.get(key)
        if roi:
            shapes.append((
                max(1, int(height * roi["height_pct"])),
                max(1, int(width * roi["width_pct"])),
            ))
    return shapes


class OCREngine:
    def __init__(self, config=None):
        self.config = config or {}
        self._engine = None
        self._lock = threading.RLock()
        
    @property
    def engine(self):
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    import os
                    perf_cfg = self.config.get("ocr_performance", {})
                    threads = int(perf_cfg.get("threads", 2))
                    threads = max(1, min(threads, 4))
                    print(f"Loading OCR Engine (First use, threads={threads})...")
                    os.environ["OMP_NUM_THREADS"] = str(threads)
                    os.environ["MKL_NUM_THREADS"] = str(threads)
                    os.environ["ONNXRUNTIME_NUM_THREADS"] = str(threads)
                    
                    from rapidocr_onnxruntime import RapidOCR
                    try:
                        self._engine = RapidOCR(intra_op_num_threads=threads)
                    except:
                        self._engine = RapidOCR()
        return self._engine
        
    def extract_text(self, image):
        # image is a cv2 bgr numpy array
        if image is None: return []
        
        with self._lock:
            result, elapse = self.engine(image)
        if result is None:
            return []
        return result

    def warm_up(self):
        """Load OCR models before the first hotkey-triggered workflow."""
        try:
            import cv2
            import numpy as np

            patient = np.zeros((110, 320, 3), dtype=np.uint8)
            for i, line in enumerate(["1968/09/27", "057Y", "M"]):
                cv2.putText(patient, line, (8, 28 + i * 32), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (240, 240, 240), 2)

            table = np.zeros((260, 720, 3), dtype=np.uint8)
            rows = [
                "Artery   Lesions   Volume/mm3   Equiv.Mass/mg   Score",
                "LM       0         0.0          0.00            0.0",
                "LAD      1         10.5         1.88            9.1",
                "CX       0         0.0          0.00            0.0",
                "RCA      0         0.0          0.00            0.0",
                "Total    1         10.5         1.88            9.1",
            ]
            for i, line in enumerate(rows):
                cv2.putText(table, line, (8, 32 + i * 36), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (235, 235, 235), 2)

            self.extract_text(patient)
            self.extract_text(table)

            monitor_size = (1920, 1080)
            try:
                import mss

                monitor_idx = int(self.config.get("monitors", {}).get("dexa_bmd", 1))
                with mss.mss() as sct:
                    if monitor_idx >= len(sct.monitors):
                        monitor_idx = 1
                    monitor = sct.monitors[monitor_idx]
                    monitor_size = (monitor["width"], monitor["height"])
            except Exception:
                pass

            for h, w in bmd_warm_up_shapes(self.config, monitor_size):
                img = np.zeros((h, w, 3), dtype=np.uint8)
                lines = [
                    "1968/09/27 074Y F",
                    "Region   BMD   T-score   Z-score",
                    "NECK     0.533  -2.9     -0.3",
                    "TOTAL    0.694  -2.0      0.3",
                ]
                for i, line in enumerate(lines):
                    y = min(h - 8, 32 + i * 38)
                    cv2.putText(img, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (235, 235, 235), 2)
                self.extract_text(img)
            print("[OCR] Warm-up complete.")
        except Exception as e:
            print(f"[OCR] Warm-up failed: {e}")
