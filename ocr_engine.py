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
            import numpy as np
            image = np.full((64, 256, 3), 255, dtype=np.uint8)
            self.extract_text(image)
            print("[OCR] Warm-up complete.")
        except Exception as e:
            print(f"[OCR] Warm-up failed: {e}")
