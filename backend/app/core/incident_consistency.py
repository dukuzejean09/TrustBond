from __future__ import annotations

from io import BytesIO
import re
from typing import Any, Dict, Optional

from PIL import Image


INCIDENT_KEYWORDS: dict[str, set[str]] = {
    "assault": {
        "assault",
        "fight",
        "beating",
        "injured",
        "attacked",
        "violence",
        "weapon",
        "blood",
        "person",
        "man",
        "woman",
    },
    "fire": {
        "fire",
        "flame",
        "smoke",
        "burn",
        "burning",
        "explosion",
        "heat",
        "ash",
    },
    "theft": {
        "theft",
        "stolen",
        "steal",
        "robbery",
        "thief",
        "burglar",
        "breakin",
        "phone",
        "wallet",
        "money",
    },
    "traffic": {
        "traffic",
        "accident",
        "crash",
        "car",
        "vehicle",
        "truck",
        "motorcycle",
        "road",
        "collision",
    },
    "vandalism": {
        "vandalism",
        "damage",
        "broken",
        "graffiti",
        "destroyed",
        "window",
        "wall",
    },
    "drug": {
        "drug",
        "narcotic",
        "substance",
        "powder",
        "deal",
        "dealer",
        "smuggling",
    },
    "fraud": {
        "fraud",
        "scam",
        "fake",
        "forgery",
        "cheat",
        "money",
        "document",
    },
    "harassment": {
        "harassment",
        "threat",
        "abuse",
        "intimidation",
        "insult",
        "person",
    },
}

# Generic words that appear across many incident narratives and should not
# trigger mismatch logic by themselves.
GENERIC_TOKENS: set[str] = {
    "person",
    "people",
    "man",
    "woman",
    "road",
    "money",
    "document",
}

STRONG_CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "assault": {"assault", "fight", "attacked", "violence", "weapon", "blood"},
    "fire": {"fire", "flame", "smoke", "burn", "burning", "explosion"},
    "theft": {"theft", "stolen", "steal", "robbery", "thief", "burglar"},
    "traffic": {"accident", "crash", "collision", "vehicle", "motorcycle", "truck"},
    "vandalism": {"vandalism", "graffiti", "broken", "destroyed"},
    "drug": {"drug", "narcotic", "dealer", "smuggling"},
    "fraud": {"fraud", "scam", "forgery", "fake"},
    "harassment": {"harassment", "threat", "abuse", "intimidation"},
}


def _normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def _incident_category(incident_type_name: Optional[str]) -> str:
    t = _normalize_text(incident_type_name)
    if any(k in t for k in ("assault", "violence", "fight", "domestic")):
        return "assault"
    if any(k in t for k in ("fire", "burn", "hazard", "explosion")):
        return "fire"
    if any(k in t for k in ("theft", "robbery", "steal", "burgl")):
        return "theft"
    if any(k in t for k in ("traffic", "accident", "crash", "road")):
        return "traffic"
    if any(k in t for k in ("vandal", "damage", "graffiti")):
        return "vandalism"
    if any(k in t for k in ("drug", "narcotic")):
        return "drug"
    if any(k in t for k in ("fraud", "scam", "forgery")):
        return "fraud"
    if any(k in t for k in ("harass", "threat", "abuse")):
        return "harassment"
    return "unknown"


def analyze_description_consistency(
    description: Optional[str],
    incident_type_name: Optional[str],
) -> Dict[str, Any]:
    category = _incident_category(incident_type_name)
    cleaned = _normalize_text(description)
    if not cleaned:
        return {
            "category": category,
            "status": "inconclusive",
            "score": 0.5,
            "reason": "no_description",
            "matched_keywords": [],
        }

    tokens = set(cleaned.split())
    expected = INCIDENT_KEYWORDS.get(category, set())
    matched = sorted(tokens.intersection(expected)) if expected else []

    other_keywords = set()
    for k, vals in INCIDENT_KEYWORDS.items():
        if k != category:
            other_keywords.update(vals)
    contradictory = sorted(tokens.intersection(other_keywords - expected) - GENERIC_TOKENS)
    strong_other = set()
    for k, vals in STRONG_CATEGORY_KEYWORDS.items():
        if k != category:
            strong_other.update(vals)
    strong_contradictory = sorted(tokens.intersection(strong_other))

    match_signal = min(1.0, len(matched) / 2.0)
    contradiction_signal = min(1.0, len(contradictory) / 3.0)
    score = max(0.0, min(1.0, 0.5 + (0.4 * match_signal) - (0.3 * contradiction_signal)))

    if category == "unknown":
        status = "inconclusive"
        reason = "unknown_incident_type"
    elif len(matched) == 0 and (
        len(strong_contradictory) >= 1 or len(contradictory) >= 2
    ):
        status = "mismatch"
        reason = "description_incident_mismatch"
    elif score >= 0.6 or len(matched) > 0:
        status = "likely_match"
        reason = "description_consistent"
    else:
        status = "inconclusive"
        reason = "insufficient_description_signal"

    return {
        "category": category,
        "status": status,
        "score": round(score, 3),
        "reason": reason,
        "matched_keywords": matched,
        "contradictory_keywords": contradictory[:8],
        "strong_contradictory_keywords": strong_contradictory[:6],
    }


def _extract_visual_signals(image_bytes: bytes) -> Dict[str, float]:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.resize((128, 128))
    pixels = list(img.getdata())
    total = max(1, len(pixels))

    warm = 0
    dark = 0
    gray = 0
    skin = 0

    for r, g, b in pixels:
        if r > 170 and g > 80 and b < 110:
            warm += 1
        if r < 55 and g < 55 and b < 55:
            dark += 1
        if abs(r - g) < 14 and abs(g - b) < 14 and r < 200:
            gray += 1
        if r > 95 and g > 40 and b > 20 and (max(r, g, b) - min(r, g, b)) > 15 and r > g and r > b:
            skin += 1

    return {
        "warm_ratio": warm / total,
        "dark_ratio": dark / total,
        "gray_ratio": gray / total,
        "skin_ratio": skin / total,
    }


def analyze_image_incident_consistency(
    image_bytes: Optional[bytes],
    incident_type_name: Optional[str],
) -> Dict[str, Any]:
    category = _incident_category(incident_type_name)
    if not image_bytes:
        return {
            "category": category,
            "status": "inconclusive",
            "score": 0.5,
            "reason": "no_image",
            "signals": {},
        }

    try:
        signals = _extract_visual_signals(image_bytes)
    except Exception:
        return {
            "category": category,
            "status": "inconclusive",
            "score": 0.5,
            "reason": "image_decode_failed",
            "signals": {},
        }

    warm = signals["warm_ratio"]
    skin = signals["skin_ratio"]
    gray = signals["gray_ratio"]
    dark = signals["dark_ratio"]

    if category == "fire":
        score = min(1.0, (warm * 1.6) + (gray * 0.4))
        if score >= 0.62:
            status = "likely_match"
            reason = "image_consistent_fire"
        elif warm < 0.03 and gray < 0.08 and dark < 0.15:
            # Strong negative signal: image is very unlikely to depict a fire scene.
            status = "mismatch"
            reason = "image_incident_mismatch"
        else:
            status = "inconclusive"
            reason = "weak_fire_signal"
    elif category == "assault":
        score = min(1.0, skin * 2.5)
        if score >= 0.35:
            status = "likely_match"
            reason = "image_consistent_assault"
        elif skin < 0.05 and gray > 0.45:
            status = "mismatch"
            reason = "image_incident_mismatch"
        else:
            status = "inconclusive"
            reason = "weak_assault_signal"
    elif category == "traffic":
        score = min(1.0, gray * 1.8)
        status = "likely_match" if score >= 0.4 else "inconclusive"
        reason = "image_consistent_traffic" if status == "likely_match" else "weak_traffic_signal"
    else:
        score = 0.5
        status = "inconclusive"
        reason = "no_visual_rule_for_incident"

    return {
        "category": category,
        "status": status,
        "score": round(float(score), 3),
        "reason": reason,
        "signals": {k: round(v, 4) for k, v in signals.items()},
    }
