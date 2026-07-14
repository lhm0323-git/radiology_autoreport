import threading

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
            print("[OCR] Warm-up complete.")
        except Exception as e:
            print(f"[OCR] Warm-up failed: {e}")
