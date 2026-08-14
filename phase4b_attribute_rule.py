import re
import ast
import json
 
 
# ---------------------------------------------------------------------------
# 1. Parse the structured data block out of `context`
# ---------------------------------------------------------------------------
 
def extract_structured_data(context: str) -> dict:
    """
    RAGTruth's business-QA contexts start with a Python-dict-literal string
    like: "\n{'name': 'X', ... 'attributes': {...}, ...}\nOverview:"
    This pulls that dict out and parses it safely with ast.literal_eval
    (safer than eval, handles Python-style dicts with single quotes/None).
    """
    match = re.search(r"\{.*\}", context, flags=re.DOTALL)
    if not match:
        return {}
    raw = match.group(0)
    # Trim to the outermost matching braces in case of trailing junk
    try:
        data = ast.literal_eval(raw)
        if isinstance(data, dict):
            return data
    except (ValueError, SyntaxError):
        pass
    return {}
 
 
# ---------------------------------------------------------------------------
# 2. Boolean/categorical attribute checks
# ---------------------------------------------------------------------------
 
# Maps a structured-data field name -> keywords to search for in the answer
# that indicate the model is making a claim about that field.
ATTRIBUTE_KEYWORDS = {
    "WiFi": ["wifi", "wi-fi", "internet access"],
    "RestaurantsReservations": ["reservation"],
    "OutdoorSeating": ["outdoor seating", "outdoor dining", "patio seating"],
    "RestaurantsTakeOut": ["takeout", "take-out", "take out"],
    "RestaurantsGoodForGroups": ["good for groups", "suitable for groups", "great for groups"],
    "Music": ["live music", "music performance", "music venue"],
    "BusinessParking": ["parking"],
}
 
# Phrases that indicate the model is asserting ABSENCE (so "no WiFi" is a
# real claim of a concrete negative value, not silence about the field)
NEGATION_PATTERNS = re.compile(
    r"\b(no|not|without|does not offer|doesn't offer|unavailable|none available)\b",
    re.IGNORECASE
)
 
 
def check_boolean_attributes(attributes: dict, answer: str) -> list:
    flags = []
    answer_lower = answer.lower()
 
    for field, keywords in ATTRIBUTE_KEYWORDS.items():
        source_value = attributes.get(field, "MISSING")
 
        for kw in keywords:
            idx = answer_lower.find(kw)
            if idx == -1:
                continue
 
            # Grab a small window of context around the keyword for review
            window_start = max(0, idx - 40)
            window_end = min(len(answer), idx + len(kw) + 40)
            snippet = answer[window_start:window_end]
 
            if source_value is None or source_value == "MISSING":
                flags.append({
                    "field": field,
                    "issue": "attribute-invention",
                    "detail": f"Answer makes a claim about '{field}' "
                              f"({kw!r}) but source value is unknown/None.",
                    "snippet": snippet,
                })
            else:
                # Source HAS a value — check for a plausible contradiction.
                # This is a coarse heuristic: if source says False/negative
                # but the answer's local phrasing doesn't contain a negation
                # word, it's likely asserting the positive incorrectly (and
                # vice versa). Not perfect, but catches clear cases cheaply.
                source_is_negative = source_value in (False, "no", "none", None)
                mentions_negation = bool(NEGATION_PATTERNS.search(snippet))
 
                if source_is_negative and not mentions_negation:
                    flags.append({
                        "field": field,
                        "issue": "attribute-contradiction",
                        "detail": f"Source says '{field}'={source_value!r} "
                                  f"(negative/false) but answer's mention "
                                  f"of {kw!r} doesn't read as a negation.",
                        "snippet": snippet,
                    })
                elif not source_is_negative and mentions_negation:
                    flags.append({
                        "field": field,
                        "issue": "attribute-contradiction",
                        "detail": f"Source says '{field}'={source_value!r} "
                                  f"(positive) but answer negates {kw!r}.",
                        "snippet": snippet,
                    })
            break  # only need one keyword hit per field
 
    return flags
 
 
# ---------------------------------------------------------------------------
# 3. Hours checks
# ---------------------------------------------------------------------------
 
def _to_12h(hour_str: str) -> str:
    """Convert '8:0' or '14:30' style source hour strings to '8:00 AM' style."""
    try:
        h, m = hour_str.split(":")
        h, m = int(h), int(m)
    except ValueError:
        return hour_str
    period = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{m:02d} {period}"
 
 
TIME_PATTERN = re.compile(
    r"\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)\b"
)
 
 
def check_hours(hours_dict: dict, answer: str) -> list:
    flags = []
    if not hours_dict:
        return flags
 
    # Collect the set of valid open/close times across the week, converted
    # to 12h strings, so we can check if the answer's stated times appear
    # anywhere in that valid set.
    valid_times = set()
    for day_range in hours_dict.values():
        if not day_range or "-" not in str(day_range):
            continue
        open_t, close_t = day_range.split("-")
        valid_times.add(_to_12h(open_t.strip()))
        valid_times.add(_to_12h(close_t.strip()))
 
    if not valid_times:
        return flags
 
    for m in TIME_PATTERN.finditer(answer):
        hour, minute, period = m.groups()
        minute = minute or "00"
        stated = f"{int(hour)}:{minute} {period.upper()}"
 
        if stated not in valid_times:
            window_start = max(0, m.start() - 40)
            window_end = min(len(answer), m.end() + 40)
            flags.append({
                "field": "hours",
                "issue": "hours-mismatch",
                "detail": f"Answer states {stated!r}, which doesn't match "
                          f"any open/close time in source hours "
                          f"{dict(hours_dict)}.",
                "snippet": answer[window_start:window_end],
            })
 
    return flags
 
 
# ---------------------------------------------------------------------------
# 4. Combined entry point
# ---------------------------------------------------------------------------
 
def check_attributes(context: str, answer: str) -> list:
    data = extract_structured_data(context)
    if not data:
        return []
 
    attributes = data.get("attributes", {}) or {}
    hours = data.get("hours", {}) or {}
 
    flags = []
    flags.extend(check_boolean_attributes(attributes, answer))
    flags.extend(check_hours(hours, answer))
    return flags
 
 
# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    demo_context = """
{'name': 'Radio Prophets', 'hours': {'Monday': '8:0-2:0', 'Tuesday': '8:0-2:0'},
 'attributes': {'WiFi': 'free', 'RestaurantsReservations': None, 'OutdoorSeating': True,
                'RestaurantsTakeOut': None, 'Music': True, 'BusinessParking': None}}
Overview:
"""
    demo_answer = (
        "They are open seven days a week from 8:00 AM to 2:00 PM and offer "
        "restaurant reservations and takeout. Parking is available in a "
        "validated garage. There is no WiFi available."
    )
 
    flags = check_attributes(demo_context, demo_answer)
    print(f"Found {len(flags)} flags:\n")
    for f in flags:
        print(f"[{f['issue']}] field={f['field']}")
        print(f"  detail: {f['detail']}")
        print(f"  snippet: {f['snippet']!r}")
        print()