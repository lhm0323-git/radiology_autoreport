import time
import ctypes
import pyperclip
from ctypes import wintypes

# Using Windows API directly for better stability
def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
    except: pass
    return ""

def send_key(vk, down=True):
    flags = 0 if down else 2
    ctypes.windll.user32.keybd_event(vk, 0, flags, 0)

def get_cursor_pos():
    point = wintypes.POINT()
    if ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):
        return point.x, point.y
    return None

def paste_to_ris(text, config):
    """
    Clears the target field and pastes new text.
    """
    if not text: return False
    paste_cfg = config.get("paste_timing", {})
    modifier_release_delay = paste_cfg.get("modifier_release_delay", 0.02)
    focus_click_delay = paste_cfg.get("focus_click_delay", 0.15)
    key_hold_delay = paste_cfg.get("key_hold_delay", 0.03)
    after_select_delay = paste_cfg.get("after_select_delay", 0.05)
    after_clear_delay = paste_cfg.get("after_clear_delay", 0.05)
    clipboard_retry_delay = paste_cfg.get("clipboard_retry_delay", 0.03)

    # Normalize line endings to Windows style (\r\n)
    text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    
    # --- Modifier Key Safety Release ---
    # Forcibly release modifier keys that might be stuck down (physically or logically)
    # 0x10=Shift, 0x11=Ctrl, 0x12=Alt, 0x5B=LWin, 0x5C=RWin
    for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]:
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0) # 2 = KEYEVENTF_KEYUP
    time.sleep(modifier_release_delay)
    # 0. Optional: Click before paste to ensure focus
    if config.get("click_before_paste", {}).get("enabled", False):
        try:
            import mss
            with mss.mss() as sct:
                m_idx = config["click_before_paste"].get("monitor_idx", 1)
                if m_idx < len(sct.monitors):
                    mon = sct.monitors[m_idx]
                    x = mon["left"] + int(mon["width"] * config["click_before_paste"].get("x_pct", 0.5))
                    y = mon["top"] + int(mon["height"] * config["click_before_paste"].get("y_pct", 0.5))
                    original_pos = get_cursor_pos()
                    ctypes.windll.user32.SetCursorPos(x, y)
                    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0) # left down
                    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0) # left up
                    time.sleep(focus_click_delay)
                    if original_pos:
                        ctypes.windll.user32.SetCursorPos(original_pos[0], original_pos[1])
        except: pass

    # 1. Copy to clipboard
    success = False
    for i in range(20):
        try:
            pyperclip.copy(text)
            # --- Verification Step ---
            v_text = pyperclip.paste()
            if v_text == text:
                print(f"[Clipboard] Data set (Unicode). Length: {len(text)}")
                print("[Clipboard] Verification PASSED ✓")
                success = True
                break
        except: 
            time.sleep(clipboard_retry_delay)
            
    if not success: 
        print("[Clipboard] Verification FAILED after 20 attempts.")
        return False

    # 2. Clear field (Ctrl+A -> Backspace)
    print("Executing Paste sequence (Ctrl+A -> Backspace -> Ctrl+V)...")
    send_key(0x11, True)  # Ctrl down
    send_key(0x41, True)  # A down
    time.sleep(key_hold_delay)
    send_key(0x41, False) # A up
    send_key(0x11, False) # Ctrl up
    
    time.sleep(after_select_delay)
    send_key(0x08, True)  # Backspace down
    send_key(0x08, False) # Backspace up
    time.sleep(after_clear_delay)

    # 3. Paste (Ctrl+V)
    send_key(0x11, True)  # Ctrl down
    send_key(0x56, True)  # V down
    time.sleep(key_hold_delay)
    send_key(0x56, False) # V up
    send_key(0x11, False) # Ctrl up
    
    print("[Paste] Sequence finished.")
    return True
