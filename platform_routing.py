import parser as p


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

SPECIAL_KEYS = {
    "scroll_lock": 0x91,
    "scrolllock": 0x91,
    "print_screen": 0x2C,
    "printscreen": 0x2C,
    "prtsc": 0x2C,
    "caps_lock": 0x14,
    "capslock": 0x14,
    "pause": 0x13,
    "insert": 0x2D,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "page_up": 0x21,
    "page_down": 0x22,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
}


def parse_hotkey(hotkey_str):
    modifiers = 0
    vk = 0
    parts = [part.strip().lower() for part in hotkey_str.split("+") if part.strip()]
    for part in parts:
        if part == "alt":
            modifiers |= MOD_ALT
        elif part in ("ctrl", "control"):
            modifiers |= MOD_CONTROL
        elif part == "shift":
            modifiers |= MOD_SHIFT
        elif part in ("win", "windows"):
            modifiers |= MOD_WIN
        elif part in SPECIAL_KEYS:
            vk = SPECIAL_KEYS[part]
        elif len(part) == 1:
            vk = ord(part.upper())
        elif part.startswith("f") and part[1:].isdigit():
            vk = 0x6F + int(part[1:])

    if vk <= 0:
        raise ValueError(f"Invalid hotkey string: {hotkey_str}")
    return modifiers, vk


def build_hotkey_task_map(config):
    """Return unified app hotkey IDs mapped to queue tasks."""
    return {
        1: ("dexa_scan_ris", None),
        2: ("dexa_toggle", None),
        3: ("bone_age", "M"),
        4: ("bone_age", "F"),
    }


def route_dexa_from_ris_lines(ris_lines, config):
    mode = p.detect_mode_from_ris(ris_lines)
    if not mode:
        return None

    monitors = config.get("monitors", {})
    if mode == "whole_body":
        monitor_idx = monitors.get("dexa_wb", 1)
    elif mode == "calcium":
        monitor_idx = monitors.get("dexa_calcium", monitors.get("dexa_bmd", 2))
    else:
        monitor_idx = monitors.get("dexa_bmd", 2)

    return (
        "dexa",
        {
            "mode": mode,
            "monitor_idx": monitor_idx,
            "is_manual": False,
        },
    )


def manual_dexa_task(mode, config):
    monitors = config.get("monitors", {})
    monitor_key = "dexa_wb" if mode == "whole_body" else "dexa_bmd"
    return (
        "dexa",
        {
            "mode": mode,
            "monitor_idx": monitors.get(monitor_key, 1 if mode == "whole_body" else 2),
            "is_manual": True,
        },
    )
