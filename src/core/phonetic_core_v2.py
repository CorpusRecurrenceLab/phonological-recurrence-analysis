"""Experimental shared core derived from archived v1. No stress inference.
Default profile: initial-only sheva, tav=t; ordinary qamats=a.
This is a computational baseline, not a reconstruction of historical speech.
"""
import sys
import re
import hashlib
import os
import json
import datetime
from perpetual_qere import normalize as normalize_perpetual_qere

# =========================
# PATHS
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))

# =========================
# CONSTANTS
# =========================

HEBREW_LETTERS = set("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")
FINAL_TO_BASE = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}

DAGESH = "\u05BC"
SHEVA = "\u05B0"
SHIN_DOT = "\u05C1"
SIN_DOT = "\u05C2"

SOF_PASUQ = "\u05C3"
ATNAH = "\u0591"
ZAQEF_KATAN = "\u0594"
ZAQEF = "\u0595"
MAQAF = "\u05BE"

GUTTURALS = {"א", "ה", "ח", "ע"}

# =========================
# CLI FLAGS
# =========================

qamats_as_o = False  # explicit baseline: ordinary qamats -> a

# =========================
# VOWELS (dynamic)
# =========================

def build_vowel_map():
    return {
        "\u05B1": "e",
        "\u05B2": "a",
        "\u05B3": "o",
        "\u05B4": "i",
        "\u05B5": "e",
        "\u05B6": "e",
        "\u05B7": "a",
        "\u05B8": "o" if qamats_as_o else "a",
        "\u05B9": "o",
        "\u05BA": "o",
        "\u05C7": "o",
        "\u05BB": "u",
    }

VOWELS = build_vowel_map()

KEEP_MARKS = set(VOWELS) | {
    DAGESH, SHEVA, SHIN_DOT, SIN_DOT,
    SOF_PASUQ, ATNAH, ZAQEF_KATAN, ZAQEF
}
VOCALIZATION_MARKS = set(VOWELS) | {DAGESH, SHEVA, SHIN_DOT, SIN_DOT}

# =========================
# UTIL
# =========================

def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def letters_only(s: str) -> str:
    return "".join(FINAL_TO_BASE.get(ch, ch) for ch in s if ch in HEBREW_LETTERS)

# =========================
# PARSING
# =========================

def parse_units(token: str):
    units = []
    i = 0
    while i < len(token):
        ch = token[i]
        if ch in HEBREW_LETTERS:
            base = FINAL_TO_BASE.get(ch, ch)
            marks = []
            j = i + 1
            while j < len(token) and token[j] not in HEBREW_LETTERS and token[j] != MAQAF:
                if token[j] in KEEP_MARKS:
                    marks.append(token[j])
                j += 1
            units.append((base, marks))
            i = j
        else:
            i += 1
    return units

def token_has_vocalization(token: str) -> bool:
    return any(ch in VOCALIZATION_MARKS for ch in token)

def unit_info(unit):
    letter, marks = unit
    return {
        "letter": letter,
        "marks": marks,
        "dagesh": DAGESH in marks,
        "sheva": SHEVA in marks,
        "shin_dot": SHIN_DOT in marks,
        "sin_dot": SIN_DOT in marks,
        "vowel_marks": [m for m in marks if m in VOWELS],
    }

def own_vowel(letter: str, info: dict) -> str:
    if letter == "ו" and info["dagesh"] and not info["vowel_marks"]:
        return "u"
    for m in info["marks"]:
        if m in VOWELS:
            return VOWELS[m]
    return ""

# =========================
# CONSONANTS
# =========================

def map_consonant(letter: str, info: dict, idx: int, n: int, ownv: str) -> str:
    if letter in ("א", "ע"):
        return ""

    if letter == "ה":
        if idx == n - 1 and not info["dagesh"] and not ownv:
            return ""
        return "h"

    if letter == "ב":
        return "b" if info["dagesh"] else "v"
    if letter == "כ":
        return "k" if info["dagesh"] else "kh"
    if letter == "פ":
        return "p" if info["dagesh"] else "f"
    if letter == "ש":
        return "s" if info["sin_dot"] else "sh"
    if letter == "צ":
        return "ts"
    if letter == "ק":
        return "q"
    if letter == "ח":
        return "h"
    if letter == "ט":
        return "t"
    if letter == "ת":
        return "t"

    if letter == "ו":
        if ownv in ("o", "u") and "\u05BA" not in info["marks"]:
            return ""
        return "v"

    if letter == "י":
        return "y"

    table = {
        "ג": "g", "ד": "d", "ז": "z", "ל": "l",
        "מ": "m", "נ": "n", "ס": "s", "ר": "r",
    }
    return table.get(letter, letter)

# =========================
# MAIN TRANSLITERATION
# =========================

def transliterate_word(token: str, sheva_mode="initial_only", return_units=False):
    if sheva_mode not in ("initial_only", "legacy_context"):
        raise ValueError("Unknown sheva mode")
    token, _ = normalize_perpetual_qere(token)
    base_letters = letters_only(token)

    name = divine_reading(token)
    if name is not None:
        return sound_units(name) if return_units else name
    if base_letters in {"אלהים", "אלוהים"}:
        return sound_units("elohim") if return_units else "elohim"

    if base_letters and not token_has_vocalization(token):
        return [] if return_units else ""

    units = parse_units(token)
    if not units:
        return [] if return_units else ""

    infos = [unit_info(u) for u in units]

    out = []
    prev_vowel = None
    n = len(units)

    for idx, (letter, marks) in enumerate(units):
        info = infos[idx]
        ownv = own_vowel(letter, info)

        next_has_sheva = idx + 1 < n and infos[idx + 1]["sheva"]
        next_letter = infos[idx + 1]["letter"] if idx + 1 < n else None
        next_ownv = own_vowel(next_letter, infos[idx + 1]) if idx + 1 < n else ""

        if letter == "י" and not ownv and not info["sheva"]:
            if not yod_carrier(infos, idx):
                out.append("y")
            continue

        if letter == "י" and ownv:
            seg = "i" if (ownv == "i" and prev_vowel == "i") else "y" + ownv
            out.append(seg)
            prev_vowel = ownv
            continue

        vowel = ""
        if ownv:
            vowel = ownv
        elif info["sheva"]:
            if idx == n - 1:
                vowel = ""
            elif idx == 0:
                vowel = "e"
            elif sheva_mode == "initial_only":
                vowel = ""
            elif infos[idx - 1]["sheva"]:
                vowel = "e"
            elif next_letter in GUTTURALS and next_ownv:
                vowel = "e"
            elif next_has_sheva:
                vowel = ""
            elif prev_vowel in ("o", "u"):
                vowel = "e"

        if idx == n - 1 and "\u05b7" in marks and (letter in ("ח", "ע") or (letter == "ה" and info["dagesh"])):
            out.append("a" + ("h" if letter == "ח" else "h" if letter == "ה" else ""))
            prev_vowel = "a"
            continue

        cons = map_consonant(letter, info, idx, n, ownv)

        seg = cons + vowel

        if seg:
            out.append(seg)
            prev_vowel = ownv or vowel

    return [u for piece in out for u in sound_units(piece)] if return_units else "".join(out)



def yod_carrier(infos, idx):
    """Declared reduced-vowel profile: unvocalized yod after i/e, or -a(y)v.
    e-monophthongization is a profile choice, not a claim about every tradition.
    """
    if idx == 0:return False
    info=infos[idx]
    if info['letter']!='י' or info['vowel_marks'] or info['sheva'] or info['dagesh']:return False
    previous=infos[idx-1]
    if any(m in previous['marks'] for m in ('\u05b4','\u05b5','\u05b6')):return True
    return (idx==len(infos)-2 and '\u05b8' in previous['marks']
            and infos[-1]['letter']=='ו' and not infos[-1]['vowel_marks']
            and not infos[-1]['sheva'] and not infos[-1]['dagesh'])


def divine_reading(token):
    units=parse_units(token);bare=''.join(x[0] for x in units)
    if not bare.endswith('יהוה'):return None
    prefix=units[:-4]
    if any(l not in 'ובכלמשה' for l,m in prefix):return None
    name='elohim' if any('\u05b4' in m for l,m in units[-4:]) else 'adonai'
    if not prefix:return name
    prefix_text=''.join(l+''.join(m) for l,m in prefix)
    pre=transliterate_word(prefix_text)
    if not pre:return None
    # The final prefix a and the initial a of the substitute coalesce.
    if name=='adonai' and pre.endswith('a'):return pre+name[1:]
    return pre+name


SOUND_PATTERN=re.compile(r'sh|kh|ts|[aeioubvgdhhztklmnsfpqry]')
def sound_units(phonetic):
    """Each digraph is one segment, never two character-based consonants."""
    units=SOUND_PATTERN.findall(phonetic)
    if ''.join(units)!=phonetic:raise ValueError('Unrecognized phonetic segment: '+phonetic)
    return units
