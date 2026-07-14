import re
import urllib.parse
import urllib.request

def _safe_console_text(text):
    encoding = getattr(__import__("sys").stdout, "encoding", None) or "utf-8"
    return str(text).encode(encoding, errors="replace").decode(encoding, errors="replace")

def group_by_lines(ocr_result, y_tolerance=20):
    if not ocr_result:
        return []
        
    lines = []
    current_line = []
    current_y = None
    
    # Sort by center Y first
    boxes = []
    for item in ocr_result:
        coords = item[0]
        text = item[1]
        center_y = sum([p[1] for p in coords]) / 4
        center_x = sum([p[0] for p in coords]) / 4
        boxes.append({"text": text, "x": center_x, "y": center_y})
        
    boxes.sort(key=lambda b: b["y"])
    
    for b in boxes:
        if current_y is None:
            current_y = b["y"]
            current_line.append(b)
        elif abs(b["y"] - current_y) <= y_tolerance:
            current_line.append(b)
            # Update average y
            current_y = sum(i["y"] for i in current_line) / len(current_line)
        else:
            current_line.sort(key=lambda i: i["x"])
            lines.append(" ".join([i["text"] for i in current_line]))
            current_line = [b]
            current_y = b["y"]
            
    if current_line:
        current_line.sort(key=lambda i: i["x"])
        lines.append(" ".join([i["text"] for i in current_line]))
        
    return lines

def parse_patient_info(ocr_results):
    lines = group_by_lines(ocr_results)
    info = {"Sex": None, "Age": None, "Menopause Age": None}
    
    for line in lines:
        line_lower = line.lower()
        line_stripped = line.strip()
        line_age = line_lower.replace('o', '0').replace('O', '0')
        
        # Extract Sex
        if info["Sex"] is None and "female" in line_lower:
            info["Sex"] = "Female"
        elif info["Sex"] is None and "male" in line_lower:
            info["Sex"] = "Male"
        elif re.search(r'\bsex\b', line_lower):
            parts = line.split(":")
            if len(parts) > 1 and parts[1].strip().lower() in ["female", "male"]:
                info["Sex"] = parts[1].strip().capitalize()

        # Extract Age
        # Handle "Age", "Ape" (OCR error), "Age:", etc.
        if re.search(r'\b(age|ape|acc)\b', line_lower) and "menopause" not in line_lower:
            nums = re.findall(r'\d+', line)
            if nums:
                info["Age"] = int(nums[-1])
                
        # Extract Menopause Age
        if "menopause" in line_lower or "meno" in line_lower:
            nums = re.findall(r'\d+', line)
            if nums:
                info["Menopause Age"] = int(nums[-1])

        if info["Age"] is None:
            age_match = re.search(r'\b[fm]?\s*0*(\d{1,3})\s*y(?:\b|[fm])', line_age)
            if age_match:
                info["Age"] = int(age_match.group(1))

        sex_token = re.search(r'(?:^|\s)([mf])(?:\s|$)|\b0*\d{1,3}\s*y\s*([mf])\b|\b([mf])\s*0*\d{1,3}\s*y\b', line_stripped, re.IGNORECASE)
        if info["Sex"] is None and sex_token:
            sex_value = next(group for group in sex_token.groups() if group)
            info["Sex"] = "Male" if sex_value.lower() == "m" else "Female"
                
    return info


def _normalize_ris_title(text):
    normalized = str(text).lower()
    normalized = normalized.replace("whble", "whole").replace("wh0le", "whole")
    normalized = normalized.replace("bdoy", "body").replace("b0dy", "body")
    normalized = re.sub(r"[\s　:：\-－_/()（）\[\]{}.,，。;；]+", "", normalized)
    return normalized


def _line_has_any(line, keywords):
    return any(keyword in line for keyword in keywords)


def _select_ris_title_text(results_lines):
    normalized_lines = [_normalize_ris_title(line) for line in results_lines if str(line).strip()]
    title_anchors = ["文字報告", "文字告", "文字", "報告", "报告"]
    title_lines = [line for line in normalized_lines if _line_has_any(line, title_anchors)]
    if title_lines:
        return " ".join(title_lines)

    exam_anchors = [
        "whole", "body", "體脂肪", "体脂肪", "脂肪分析",
        "bmd", "骨質密度", "骨质密度", "骨密度", "骨密",
        "calcium", "agatston", "鈣化", "钙化", "化指",
    ]
    exam_lines = [line for line in normalized_lines if _line_has_any(line, exam_anchors)]
    return " ".join(exam_lines)


def detect_mode_from_ris_title(results_lines):
    title = _select_ris_title_text(results_lines)
    if not title:
        return None

    calcium = _line_has_any(title, ["calcium", "agatston", "鈣化", "钙化", "化指"])
    whole_body = _line_has_any(title, [
        "wholebody", "whole", "body",
        "體脂肪", "体脂肪", "脂肪分析",
        "骨密體脂肪", "骨密体脂肪",
        "bodycomposition",
    ])
    bmd = _line_has_any(title, ["bmd", "bonedensity", "骨質密度", "骨质密度", "骨密度"])
    weak_bmd = "骨密" in title and not whole_body

    if calcium:
        return "calcium"
    if whole_body:
        return "whole_body"
    if bmd or weak_bmd:
        return "bmd"
    return None


def detect_mode_from_ris(results_lines):
    print("\n--- RIS Screen Text (Auto-detect) ---")
    for line in results_lines:
        print(f"  {_safe_console_text(line)}")
    print("-------------------------------------")

    mode = detect_mode_from_ris_title(results_lines)
    print(f"[RIS Title Mode Detection] mode={mode}")
    return mode

    text = " ".join(results_lines).lower()
    bmd_score = 0
    wb_score = 0
    calcium_score = 0
    if any(k in text for k in [
        "whole body",
        "body composition",
        "total body fat",
        "body fat percentage",
        "fat percentage",
        "體脂肪",
        "体脂肪",
        "骨密體脂肪",
        "骨密体脂肪",
    ]):
        wb_score += 10
    if any(k in text for k in ["calcium score", "calcium scoring", "鈣化指數", "钙化指数"]):
        calcium_score += 10
    
    # Stricter keywords exact to user request
    bmd_keywords = ["bmd", "骨質"] 
    wb_keywords = ["whole body"]
    calcium_keywords = ["鈣化指數", "钙化指数", "calcium score", "calcium scoring"]
    
    for k in bmd_keywords:
        if k in text: bmd_score += 1
    for k in wb_keywords:
        if k in text: wb_score += 1
    for k in calcium_keywords:
        if k in text: calcium_score += 1
    if ("鈣化" in text or "钙化" in text) and ("指數" in text or "指数" in text):
        calcium_score += 1
        
    print(f"[RIS Mode Detection] BMD Score: {bmd_score}, WB Score: {wb_score}, Calcium Score: {calcium_score}")
        
    if calcium_score > 0: return "calcium"
    if wb_score > 0: return "whole_body"
    if bmd_score > 0: return "bmd"
    return None

def detect_mode(ocr_results):
    lines = group_by_lines(ocr_results)
    text = " ".join(lines).lower()
    
    # Weighted detection
    bmd_score = 0
    wb_score = 0
    
    bmd_keywords = ["t-score", "z-score", "bmd", "bone density", "region", "l1-l4", "neck", "hip", "total l1", "骨質", "密度"]
    wb_keywords = ["fat", "vat", "lean", "adipose", "android", "gynoid", "total body %", "composition", "mass", "脂肪", "組成"]
    
    for k in bmd_keywords:
        if k in text: bmd_score += 1
    for k in wb_keywords:
        if k in text: wb_score += 1
        
    print(f"[Mode Detection] BMD Score: {bmd_score}, WB Score: {wb_score}")
    
    if wb_score > bmd_score:
        return "whole_body"
    return "bmd"

def parse_whole_body(ocr_results):
    lines = group_by_lines(ocr_results)
    data = {
        "fat_percent": None,
        "vat_area": None,
        "lean_index": None,
        "ag_ratio": None
    }
    
    text = "\n".join(lines).lower()
    
    # 1. Total body fat percentage (Robust non-greedy skip)
    m = re.search(r"total\s*body\s*%?\s*fat.*?([-+]?\d*\.\d+|\d+)", text, re.DOTALL)
    if m: data["fat_percent"] = float(m.group(1))
    
    # 2. VAT area (Handles Est. VAT Area (cm2) etc.)
    m = re.search(r"vat\s*area.*?([-+]?\d*\.\d+|\d+)", text, re.DOTALL)
    if m: data["vat_area"] = float(m.group(1))
    
    # 3. Appendicular Lean (muscle mass) index
    m = re.search(r"appen\.*\s*lean.*?([-+]?\d*\.\d+|\d+)", text, re.DOTALL)
    if m: data["lean_index"] = float(m.group(1))
    
    # 4. Android/Gynoid Ratio
    m = re.search(r"android\s*/?\s*gynoid.*?([-+]?\d*\.\d+|\d+)", text, re.DOTALL)
    if m: data["ag_ratio"] = float(m.group(1))
    
    # Validation flag
    data["is_valid"] = any(v is not None for v in [data["fat_percent"], data["vat_area"], data["lean_index"]])
    
    # --- Diagnostics for User ---
    print("\n--- Whole Body Diagnostics ---")
    print(f"Fat %: {data['fat_percent']}")
    print(f"VAT Area: {data['vat_area']}")
    print(f"Lean Index: {data['lean_index']}")
    print(f"AG Ratio: {data['ag_ratio']}")
    print("------------------------------\n")
    
    return data

def _row_center_y(box):
    return (box[0][1] + box[2][1]) / 2

def _box_center_x(box):
    return (box[0][0] + box[1][0]) / 2

def _parse_score_number(text):
    cleaned = text.strip().replace(",", ".").replace("O", "0").replace("o", "0")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None

def _parse_score_numbers(text):
    cleaned = text.strip().replace(",", ".").replace("O", "0").replace("o", "0")
    values = []
    for match in re.finditer(r"[-+]?\d+(?:\.\d+)?", cleaned):
        try:
            values.append(float(match.group(0)))
        except ValueError:
            continue
    return values

def _group_ocr_rows(ocr_results, y_tolerance=18):
    rows = []
    for item in ocr_results or []:
        if len(item) < 2:
            continue
        box, text = item[0], str(item[1])
        y_center = _row_center_y(box)
        for row in rows:
            if abs(y_center - row["y"]) <= y_tolerance:
                row["items"].append((box, text))
                row["y"] = sum(_row_center_y(i[0]) for i in row["items"]) / len(row["items"])
                break
        else:
            rows.append({"y": y_center, "items": [(box, text)]})

    for row in rows:
        row["items"].sort(key=lambda item: _box_center_x(item[0]))
    rows.sort(key=lambda row: row["y"])
    return rows

def parse_calcium_scores(ocr_results):
    """
    Parse the coronary calcium table and return only LM/LAD/CX/RCA/Total scores.
    """
    vessels = ("LM", "LAD", "CX", "RCA", "Total")
    data = {vessel: None for vessel in vessels}
    vessel_y = {}
    unlabeled_scores = []
    rows = _group_ocr_rows(ocr_results)

    score_x = None
    for row in rows:
        for box, text in row["items"]:
            if "score" in text.lower().replace(" ", ""):
                score_x = _box_center_x(box)
                print(f"[Calcium] Score column detected at x={score_x:.1f}")
                break
        if score_x is not None:
            break

    for row in rows:
        row_text = " ".join(text for _, text in row["items"])
        normalized = row_text.lower().replace(" ", "")

        vessel = None
        if re.search(r"\bl\s*\.?\s*(main|m)\b|\blm\b", row_text, re.IGNORECASE):
            vessel = "LM"
        elif re.search(r"\blad\b", row_text, re.IGNORECASE):
            vessel = "LAD"
        elif re.search(r"\bl?cx\b", row_text, re.IGNORECASE):
            vessel = "CX"
        elif re.search(r"\brca\b", row_text, re.IGNORECASE):
            vessel = "RCA"
        elif "total" in normalized:
            vessel = "Total"

        candidates = []
        for box, text in row["items"]:
            values = _parse_score_numbers(text)
            if values:
                value = values[-1] if len(values) > 1 else values[0]
                candidates.append((_box_center_x(box), value, text))
        if not candidates:
            continue

        if score_x is not None:
            _, value, raw_text = min(candidates, key=lambda item: abs(item[0] - score_x))
        else:
            _, value, raw_text = max(candidates, key=lambda item: item[0])

        if vessel is None:
            unlabeled_scores.append((row["y"], value, raw_text))
            continue

        data[vessel] = value
        vessel_y[vessel] = row["y"]
        print(f"[Calcium] {vessel}: {value} from '{raw_text}'")

    if data["CX"] is None and "LAD" in vessel_y and "RCA" in vessel_y:
        low, high = sorted((vessel_y["LAD"], vessel_y["RCA"]))
        between = [item for item in unlabeled_scores if low < item[0] < high]
        if between:
            _, value, raw_text = between[0]
            data["CX"] = value
            print(f"[Calcium] CX: {value} from unlabeled row '{raw_text}'")

    data["is_valid"] = all(data[vessel] is not None for vessel in vessels)
    return data

def parse_bmd_v2(ocr_results):
    """
    Advanced coordinate-based parsing for BMD tables.
    Uses Column Ranges (Left to Right) for robust intersection.
    """
    data = {"t_score": None, "z_score": None, "has_neck": False}
    
    # 1. Map columns (find horizontal ranges of headers)
    col_reg = None
    col_t = None
    col_z = None
    
    print("\n--- BMD Column Detection Diagnostics ---")
    for box, text, score in ocr_results:
        t_clean = text.lower().replace(" ", "").replace("-", "")
        left, right = box[0][0], box[1][0]
        cx = (left + right) / 2
        
        # Priority: Region (Label)
        if "region" in t_clean:
            col_reg = (left, right, cx)
            print(f"Set Region-Column: '{text}' @ [{left:.1f}-{right:.1f}]")

        # Priority 1: Exact 'T-score'. PR/Peak Reference is a percent column,
        # not a T-score fallback.
        if "tscore" in t_clean and not "pr" in t_clean:
            col_t = (left, right, cx)
            print(f"Set T-Column (Primary): '{text}' @ [{left:.1f}-{right:.1f}]")
            
        # Priority 1: Exact 'Z-score'. AM/Age Matched is a percent column,
        # not a Z-score fallback.
        if "zscore" in t_clean and not "am" in t_clean:
            col_z = (left, right, cx)
            print(f"Set Z-Column (Primary): '{text}' @ [{left:.1f}-{right:.1f}]")

    # 2. Group by lines to identify rows (use a slightly larger threshold)
    rows = [] 
    for box, text, score in ocr_results:
        y_center = (box[0][1] + box[2][1]) / 2
        added = False
        for row_y, items in rows:
            if abs(y_center - row_y) < 20: # Restored to 20 to prevent merging with metadata row below
                items.append((box, text))
                added = True
                break
        if not added:
            rows.append((y_center, [(box, text)]))
            
    # 3. Process Rows
    all_t, all_z = [], []
    neck_t, neck_z = None, None
    one_third_t, one_third_z = None, None
    total_t, total_z = None, None
    
    # Pre-defined region keywords for fuzzy matching
    target_keywords = ["l1", "l2", "l3", "l4", "neck", "total", "1/3", "mid", "ud", "spine", "hip", "radius"]
    
    print("\n--- BMD Row Alignment Diagnostics ---")
    for row_y, items in rows:
        # Sort items in this row by X coordinate for sequential logic
        items.sort(key=lambda x: x[0][0][0])
        row_text = " ".join([it[1].lower() for it in items])
        
        # 3a. METADATA FILTER: Strictly exclude any row that looks like noise or summary stats
        # This prevents picking data from the "Total BMD CV 1.0%" row
        if any(k in row_text for k in [
            "cv", "acf", "bcf", "%", "=", "fracture", "classification",
            "region", "t-score", "z-score", "peak reference", "age matched",
            "bmd[g/cm", "bmd [g/cm", "area [", "bmc",
        ]):
            continue
            
        if "neck" in row_text: data["has_neck"] = True
        
        # 3b. Extract all numbers and their horizontal centers
        candidates = []
        for box, text in items:
            # Match floats and integers
            found_nums = re.findall(r"([-+]?\d*\.\d+|\d+)", text)
            for val_str in found_nums:
                cx = (box[0][0] + box[1][0]) / 2
                is_bmd = "." in val_str and len(val_str.split(".")[1]) >= 3
                candidates.append({
                    "cx": cx, 
                    "val": float(val_str), 
                    "str": val_str,
                    "is_bmd": is_bmd
                })
        
        if not candidates: continue
        
        # 3c. IDENTIFY REGION: Fuzzy matching + Column alignment
        row_label = "unknown"
        if col_reg:
            reg_items = []
            for box, text in items:
                c_cx = (box[0][0] + box[1][0]) / 2
                if abs(c_cx - col_reg[2]) < 100:
                    reg_items.append(text.lower().strip())
            if reg_items:
                full_reg_text = " ".join(reg_items)
                for k in target_keywords:
                    if k in full_reg_text:
                        row_label = k
                        break
        
        if row_label == "unknown":
            for k in target_keywords:
                if k in row_text:
                    row_label = k
                    break

        # 3d. ASSIGN T/Z: Hybrid Logic (Nearest Neighbor + Sequential Backup)
        row_t_val, row_z_val = None, None
        
        # Filter for reasonable T/Z candidates (exclude 3-decimal BMDs and extremes)
        valid_candidates = [c for c in candidates if not c["is_bmd"] and -10 < c["val"] < 10]
        
        if valid_candidates:
            # 1. Try Coordinate Matching
            if col_t:
                best_t = min(valid_candidates, key=lambda c: abs(c["cx"] - col_t[2]))
                if abs(best_t["cx"] - col_t[2]) < 120:
                    row_t_val = best_t["val"]
            
            if col_z:
                best_z = min(valid_candidates, key=lambda c: abs(c["cx"] - col_z[2]))
                if abs(best_z["cx"] - col_z[2]) < 120:
                    row_z_val = best_z["val"]
            
            # 2. Sequential Backup: If coordinate matching is missing one, use position
            # In BMD rows: Area(0), BMC(1), BMD(2), T(3), PR(4), Z(5), AM(6)
            # The candidates list is already X-sorted.
            if (row_t_val is None or row_z_val is None) and len(candidates) >= 6:
                # Indices for T and Z in a full row of 7 items
                # We use -4 and -2 from the end as backup (T, PR, Z, AM)
                if row_t_val is None: row_t_val = candidates[-4]["val"]
                if row_z_val is None: row_z_val = candidates[-2]["val"]

        if row_label != "unknown" and row_t_val is not None and row_z_val is not None:
            all_t.append(row_t_val)
            all_z.append(row_z_val)
        
        if row_t_val is not None or row_z_val is not None:
            display_label = row_label.upper() if row_label != "unknown" else f"Row@{int(row_y)}"
            print(f"Row '{display_label}': Assigned T={row_t_val}, Z={row_z_val}")
        
        l_row_label = row_label.lower()
        if "neck" in l_row_label: neck_t, neck_z = row_t_val, row_z_val
        if "1/3" in l_row_label: one_third_t, one_third_z = row_t_val, row_z_val
        if "total" in l_row_label: total_t, total_z = row_t_val, row_z_val

    # 4. Final Selection Priority: Neck > 1/3 > Total
    if neck_t is not None:
        data["t_score"], data["z_score"] = neck_t, neck_z
    elif one_third_t is not None:
        data["t_score"], data["z_score"] = one_third_t, one_third_z
    elif total_t is not None:
        data["t_score"], data["z_score"] = total_t, total_z
    elif all_t:
        # Final Fallback: Use the last identified row if keywords failed
        data["t_score"], data["z_score"] = all_t[-1], all_z[-1]
        print(f"Fallback: Using LAST identified data row values (T={data['t_score']}, Z={data['z_score']})")
        
    print(f"Final Selection: T={data['t_score']}, Z={data['z_score']}\n")
    data["is_valid"] = data["t_score"] is not None
    return data
        
    print(f"Final Selection: T={data['t_score']}, Z={data['z_score']}\n")
    data["is_valid"] = data["t_score"] is not None
    return data

MESA_CALCIUM_URL = "https://tools.mesa-nhlbi.org/Calcium/input.aspx"
MESA_RACE_VALUES = {"black": "0", "chinese": "1", "hispanic": "2", "white": "3"}


def _mesa_gender_value(sex):
    text = str(sex or "").strip().lower()
    if text.startswith("f"):
        return "0"
    if text.startswith("m"):
        return "1"
    return None


def _html_input_value(html_text, name):
    tag_match = re.search(rf'<input\b[^>]*\bname="{re.escape(name)}"[^>]*>', html_text, re.IGNORECASE)
    if not tag_match:
        return ""
    value_match = re.search(r'\bvalue="([^"]*)"', tag_match.group(0), re.IGNORECASE)
    return value_match.group(1) if value_match else ""


def parse_mesa_percentile_html(html_text):
    match = re.search(r'id="percLabel"[^>]*>(.*?)</span>', html_text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
    number = re.search(r"[0-9]+(?:\.[0-9]+)?", text)
    return int(round(float(number.group(0)))) if number else None


def fetch_mesa_percentile(age, sex, score, race="chinese", timeout=3):
    if age is None or score is None:
        print(f"[MESA] percentile lookup skipped: missing age or score (age={age}, score={score})")
        return None
    age = int(age)
    if age < 45 or age > 84:
        print(f"[MESA] percentile lookup skipped: age out of supported range ({age})")
        return None
    gender = _mesa_gender_value(sex)
    race_value = MESA_RACE_VALUES.get(str(race or "chinese").strip().lower())
    if gender is None or race_value is None:
        print(f"[MESA] percentile lookup skipped: missing sex or unsupported race (sex={sex}, race={race})")
        return None

    with urllib.request.urlopen(MESA_CALCIUM_URL, timeout=timeout) as response:
        page = response.read().decode("utf-8", errors="replace")
    form = {
        "__VIEWSTATE": _html_input_value(page, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _html_input_value(page, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _html_input_value(page, "__EVENTVALIDATION"),
        "Age": str(age),
        "gender": gender,
        "Race": race_value,
        "Score": str(score),
        "Calculate": "Calculate",
        "SmartScroller1_ScrollX": "0",
        "SmartScroller1_ScrollY": "0",
        "SmartScroller2_ScrollX": "0",
        "SmartScroller2_ScrollY": "0",
    }
    data = urllib.parse.urlencode(form).encode("ascii")
    request = urllib.request.Request(MESA_CALCIUM_URL, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = response.read().decode("utf-8", errors="replace")
    return parse_mesa_percentile_html(result)


def add_mesa_percentile(patient_info, results_data, race="chinese"):
    try:
        percentile = fetch_mesa_percentile(patient_info.get("Age"), patient_info.get("Sex"), results_data.get("Total"), race=race)
    except Exception as exc:
        print(f"[MESA] percentile lookup skipped: {exc}")
        return results_data
    if percentile is not None:
        results_data["mesa_percentile"] = percentile
        print(f"[MESA] percentile={percentile}%")
    return results_data


def append_mesa_to_calcium_report(report, total, percentile):
    if percentile is None or "MESA" in report:
        return report
    total_text = str(total)
    pattern = rf"(Total Calcium Score was\s+{re.escape(total_text)})(?![,\d.])"
    return re.sub(pattern, rf"\1, MESA {int(percentile)}%", report)


def apply_clinical_logic(patient_info, mode, results_data, config, force_toggle=False):
    # Get templates from config
    templates = config.get("templates", {})
    
    if mode == "whole_body":
        fat_percent = results_data.get("fat_percent")
        sex = patient_info.get("Sex")
        fat_result = "N/A"
        
        if fat_percent is not None:
            if sex == "Male":
                if fat_percent < 23: fat_result = "Normal"
                elif fat_percent <= 35: fat_result = "Overweight"
                else: fat_result = "Obesity"
            else: # Female
                if fat_percent < 25: fat_result = "Normal"
                elif fat_percent <= 38: fat_result = "Overweight"
                else: fat_result = "Obesity"
                
        # 2. VAT area
        vat_area = results_data.get("vat_area")
        vat_result = "Unknown"
        if vat_area is not None:
            if vat_area < 100: vat_result = "Normal"
            elif vat_area < 160: vat_result = "Increased"
            else: vat_result = "High"
            
        # 3. Appendicular Lean/Height2
        lean_index = results_data.get("lean_index")
        lean_result = "Unknown"
        if lean_index is not None:
            if sex == "Male":
                if lean_index < 7.0: lean_result = "Low lean mass"
                else: lean_result = "Normal"
            else: # Female
                if lean_index < 5.4: lean_result = "Low lean mass"
                else: lean_result = "Normal"
                
        # 4. Android/Gynoid Ratio
        ag_ratio = results_data.get("ag_ratio")
        ag_result = "Unknown"
        if ag_ratio is not None:
            if ag_ratio >= 1: ag_result = "Apple-shape"
            else: ag_result = "Pear-shape"
            
        # --- Diagnostics for User ---
        print("\n--- Whole Body Clinical Logic ---")
        print(f"Fat Result: {fat_result}")
        print(f"VAT Result: {vat_result}")
        print(f"Lean Result: {lean_result}")
        print(f"AG Result: {ag_result}")
        print("---------------------------------\n")

        template = config.get("whole_body_template", "").replace("\n", "\r\n")
        report = template.format(
            fat_percent=fat_percent if fat_percent is not None else "N/A",
            fat_result=fat_result,
            vat_area=vat_area if vat_area is not None else "N/A",
            vat_result=vat_result,
            lean_index=lean_index if lean_index is not None else "N/A",
            lean_result=lean_result,
            ag_ratio=ag_ratio if ag_ratio is not None else "N/A",
            ag_result=ag_result
        )
        return report, results_data

    if mode == "calcium":
        def fmt(value):
            if value is None:
                return "N/A"
            if isinstance(value, (int, float)) and float(value).is_integer():
                return str(int(value))
            return f"{value:.1f}"

        values = {
            "LM": fmt(results_data.get("LM")),
            "LAD": fmt(results_data.get("LAD")),
            "CX": fmt(results_data.get("CX")),
            "LCX": fmt(results_data.get("CX")),
            "RCA": fmt(results_data.get("RCA")),
            "Total": fmt(results_data.get("Total")),
        }
        template = config.get(
            "calcium_template",
            templates.get(
                "calcium",
                "Agatston Score (Calcium Score)\n"
                "------------------------------\n"
                "L.MAIN:  {LM}\n"
                "LAD   :  {LAD}\n"
                "LCX   :  {CX}\n"
                "RCA   :  {RCA}\n"
                "------------------------------\n"
                "Total :  {Total}\n"
                "Total Calcium Score was {Total}",
            ),
        ).replace("\n", "\r\n")
        report = template.format(**values)
        report = append_mesa_to_calcium_report(report, values["Total"], results_data.get("mesa_percentile"))
        return report, results_data

    else: # BMD
        age = patient_info.get("Age")
        sex = patient_info.get("Sex")
        menopause_age = patient_info.get("Menopause Age")
        has_neck = results_data.get("has_neck", False)
        
        use_t_score = False
        if sex == "Male":
            if age is not None and age >= 50:
                use_t_score = True
        else: # Female
            if menopause_age is not None:
                use_t_score = True
            elif age is not None and age >= 55: # If age is very high, assume postmenopausal
                use_t_score = True

        # --- Manual Toggle Override ---
        decision_suffix = ""
        if force_toggle:
            use_t_score = not use_t_score
            decision_suffix = "(toggled)"
        # ------------------------------
        
        # --- Diagnostics for User ---
        print("\n--- Patient Demographics Diagnostics ---")
        print(f"Sex: {sex}")
        print(f"Age: {age}")
        print(f"Menopause Age: {menopause_age}")
        print(f"Decision: {'T-score' if use_t_score else 'Z-score'} mode{decision_suffix}")
        print("------------------------------------------\n")
            
        t_score = results_data.get("t_score")
        z_score = results_data.get("z_score")
        
        classification = "Unknown"
        score_type = "T-score" if use_t_score else "Z-score"
        score_value = t_score if use_t_score else z_score
        
        if score_value is not None:
            if use_t_score:
                if score_value >= -1.0: classification = "骨質正常( normal )"
                elif score_value > -2.5: classification = "低骨量 ( low bone mass )"
                else: classification = "骨質疏鬆( osteoporosis )"
            else:
                if score_value <= -2.0: classification = "低於同齡預期值( below the expected range for age )"
                else: classification = "介於同齡的預期值( within the expected range for age )"
        else:
            score_value = "N/A"
        
        # Build bracket notation for scan sites
        if has_neck:
            sites_line = "L-spine Total / (Femoral Neck) / Total Hip"
        else:
            sites_line = "(L-spine Total) / Femoral Neck / Total Hip"
        
        # Build header line
        if use_t_score:
            header = "[for Postmenopausal women / Men age >= 50]"
        else:
            header = "[for Premenopausal women / Men < 50]"
        
        # Format score value (no internal space between - and number)
        if isinstance(score_value, (int, float)):
            score_str = str(score_value)
        else:
            score_str = str(score_value)
        
        # Build the full report with precise spacing requested
        report_lines = [
            header,
            "",
            f"The lowest {score_type} among {sites_line}",
            "",
            f"=  {score_str} ",
            "",
            f"Conclusion : {classification}",
            "",
            "1. 本報告參考 ISCD (International Society for Clinical Densitometry) 及中華民國骨鬆症醫學會指引，旨在提供臨床醫師最直覺的診斷數據。",
            "",
            "2. [Postmenopausal women / Men age >= 50] 停經後婦女和50 歲以上男性的骨密度診斷標準採用T值，且用白人女性平均值為台灣男女性T值參考資料庫。T >= -1.0 骨質正常(Normal); -2.5 < T < -1.0 低骨量 ( low bone mass ); T <= -2.5 骨質疏鬆(Osteoporosis)",
            "",
            "3. [Premenopausal women / Men < 50] 停經前婦女和低於50 歲男性的骨密度報告採用Z值，而非T值. 當Z值等於或小於-2.0 時稱之為低於同齡的預期值(below the expected range for age)，當Z值大於-2.0 時稱之為介於同齡的預期值(within the expected range for age)。",
        ]
        
        report = "\r\n".join(report_lines)
        return report, {"score_type": score_type, "score_value": score_value, "classification": classification, "has_neck": has_neck}
