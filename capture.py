import mss
import mss.tools
import numpy as np
import cv2

def capture_screen_rois(monitor_idx, config, mode=None):
    """
    Capture patient info and results ROIs using mss (Physical Pixels).
    """
    with mss.mss() as sct:
        # mss monitor_idx is 1-based. 0 is all monitors.
        if monitor_idx >= len(sct.monitors):
            monitor_idx = 1
            
        monitor = sct.monitors[monitor_idx]
        # Grab physical pixels
        screenshot = np.array(sct.grab(monitor))
        
        # Determine which ROI config to use
        if mode == "bmd" and "roi_bmd" in config:
            pi_cfg = config["roi_bmd"]["patient_info"]
            rs_cfg = config["roi_bmd"]["results"]
        elif mode == "calcium" and "roi_calcium" in config:
            pi_cfg = config["roi_calcium"]["patient_info"]
            rs_cfg = config["roi_calcium"]["results"]
        elif mode == "calcium":
            print("[Capture] Missing roi_calcium. Please run Calcium Table calibration.")
            return None, None
        elif mode == "whole_body" and "roi_wb" in config:
            pi_cfg = config["roi_wb"]["patient_info"]
            rs_cfg = config["roi_wb"]["results"]
        else:
            # Legacy fallback
            pi_cfg = config.get("roi_patient_info", {"left_pct": 0.0, "top_pct": 0.15, "width_pct": 0.35, "height_pct": 0.35})
            rs_cfg = config.get("roi_results_summary", {"left_pct": 0.3, "top_pct": 0.5, "width_pct": 0.65, "height_pct": 0.4})
        
        # Use physical monitor dimensions from mss
        width = monitor["width"]
        height = monitor["height"]
        
        pi_left = int(width * pi_cfg["left_pct"])
        pi_top = int(height * pi_cfg["top_pct"])
        pi_width = int(width * pi_cfg["width_pct"])
        pi_height = int(height * pi_cfg["height_pct"])
        patient_img = screenshot[pi_top:pi_top+pi_height, pi_left:pi_left+pi_width]
        
        rs_left = int(width * rs_cfg["left_pct"])
        rs_top = int(height * rs_cfg["top_pct"])
        rs_width = int(width * rs_cfg["width_pct"])
        rs_height = int(height * rs_cfg["height_pct"])
        results_img = screenshot[rs_top:rs_top+rs_height, rs_left:rs_left+rs_width]
        
        # Convert BGRA (mss) to BGR (cv2)
        patient_img = cv2.cvtColor(patient_img, cv2.COLOR_BGRA2BGR)
        results_img = cv2.cvtColor(results_img, cv2.COLOR_BGRA2BGR)
        
        return patient_img, results_img


def capture_bone_age_roi(monitor_idx, config):
    with mss.mss() as sct:
        if monitor_idx >= len(sct.monitors):
            monitor_idx = 1

        monitor = sct.monitors[monitor_idx]
        screenshot = np.array(sct.grab(monitor))

        roi_cfg = config.get(
            "roi_bone_age",
            {"left_pct": 0.0, "top_pct": 0.0, "width_pct": 1.0, "height_pct": 0.8},
        )
        left = int(monitor["width"] * roi_cfg["left_pct"])
        top = int(monitor["height"] * roi_cfg["top_pct"])
        width = int(monitor["width"] * roi_cfg["width_pct"])
        height = int(monitor["height"] * roi_cfg["height_pct"])

        img = screenshot[top:top + height, left:left + width]
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
