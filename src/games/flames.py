"""Pure FLAMES logic - no Telegram, no database. Fully deterministic."""
from __future__ import annotations

import hashlib
import unicodedata
from collections import Counter
from dataclasses import dataclass

FLAMES = "FLAMES"
LABELS = {"F": "Friends", "L": "Lovers", "A": "Affection", "M": "Marriage", "E": "Enemies", "S": "Siblings"}

# compatibility % range per result (a stable hash of the names picks the value)
_RANGES = {"F": (45, 85), "L": (70, 99), "A": (60, 92), "M": (75, 99), "E": (5, 40), "S": (35, 75)}


def normalize(name: str) -> str:
    """lower-case, drop spaces / digits / punctuation / emoji (letters and letter-marks stay)."""
    return "".join(
        ch for ch in name.lower() if ch.isalpha() or unicodedata.category(ch) in ("Mn", "Mc")
    )


@dataclass(frozen=True)
class Elimination:
    removed: str
    remaining: tuple


@dataclass(frozen=True)
class FlamesResult:
    name1: str            # normalised
    name2: str
    mask1: tuple          # True = letter was cancelled
    mask2: tuple
    remaining: int        # unmatched letters
    steps: tuple          # tuple[Elimination]
    letter: str
    percent: int

    @property
    def label(self) -> str:
        return LABELS[self.letter]


def cancel_common(a: str, b: str):
    common = Counter(a) & Counter(b)

    def mask(s: str):
        left, out = Counter(common), []
        for ch in s:
            if left[ch] > 0:
                left[ch] -= 1
                out.append(True)
            else:
                out.append(False)
        return tuple(out)

    remaining = len(a) + len(b) - 2 * sum(common.values())
    return mask(a), mask(b), remaining


def eliminate(count: int):
    """Circular elimination. count == 0 (identical names) is a 'perfect match' -> M."""
    if count <= 0:
        return "M", ()
    letters, idx, steps = list(FLAMES), 0, []
    while len(letters) > 1:
        idx = (idx + count - 1) % len(letters)
        removed = letters.pop(idx)
        steps.append(Elimination(removed, tuple(letters)))
    return letters[0], tuple(steps)


def compatibility(letter: str, a: str, b: str) -> int:
    key = "|".join(sorted((a, b)))
    h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    lo, hi = _RANGES[letter]
    return lo + h % (hi - lo + 1)


def calculate(name1: str, name2: str) -> FlamesResult:
    a, b = normalize(name1), normalize(name2)
    if not a or not b:
        raise ValueError("both names need at least one letter")
    m1, m2, remaining = cancel_common(a, b)
    letter, steps = eliminate(remaining)
    return FlamesResult(a, b, m1, m2, remaining, steps, letter, compatibility(letter, a, b))
