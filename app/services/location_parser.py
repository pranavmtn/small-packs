"""Location text parser.

Converts free-form location strings into structured JSON path arrays.
Simple heuristics for v1 — AI will replace this later.
"""

from __future__ import annotations

import re
from typing import List


class LocationParser:
    """Parse free-text location strings into title-cased path segments."""

    # Explicit separators users may type
    SEPARATOR_PATTERN = re.compile(r"\s*(?:>|/|\||→|->|,)\s*")

    # Ordinal / position adjectives that often start a path segment
    POSITION_WORDS = {
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "top",
        "bottom",
        "middle",
        "upper",
        "lower",
        "left",
        "right",
        "front",
        "back",
        "inner",
        "outer",
    }

    # Container / surface nouns that often end a path segment
    CONTAINER_WORDS = {
        "box",
        "boxes",
        "shelf",
        "shelves",
        "level",
        "levels",
        "drawer",
        "drawers",
        "cabinet",
        "cabinets",
        "cupboard",
        "cupboards",
        "closet",
        "closets",
        "bin",
        "bins",
        "bag",
        "bags",
        "rack",
        "racks",
        "row",
        "rows",
        "column",
        "columns",
        "compartment",
        "compartments",
        "crate",
        "crates",
        "trunk",
        "trunks",
        "locker",
        "lockers",
        "room",
        "area",
        "section",
        "zone",
        "aisle",
        "bay",
        "slot",
        "hook",
        "peg",
        "wall",
        "floor",
        "ceiling",
        "corner",
        "side",
        "stack",
        "pile",
        "shelf",
    }

    # Multi-word container phrases (matched as a unit)
    CONTAINER_PHRASES = [
        "top shelf",
        "bottom shelf",
        "middle shelf",
        "upper shelf",
        "lower shelf",
        "first box",
        "second box",
        "third box",
        "first level",
        "second level",
        "third level",
        "top drawer",
        "bottom drawer",
        "middle drawer",
        "left side",
        "right side",
    ]

    def parse(self, text: str) -> List[str]:
        """Parse location text into a list of path segments."""
        if not text or not str(text).strip():
            return []

        cleaned = re.sub(r"\s+", " ", str(text).strip())

        # Prefer explicit separators when present
        if self.SEPARATOR_PATTERN.search(cleaned):
            parts = [p for p in self.SEPARATOR_PATTERN.split(cleaned) if p.strip()]
            return [self._title_case(p) for p in parts]

        return self._heuristic_split(cleaned)

    def _heuristic_split(self, text: str) -> List[str]:
        """Split free text using container/position heuristics."""
        lower = text.lower()
        tokens = lower.split()

        if len(tokens) <= 1:
            return [self._title_case(text)]

        # Find start indices of container-like segments from the right
        segment_starts: List[int] = []
        i = 0
        while i < len(tokens):
            # Two-word phrase match
            if i + 1 < len(tokens):
                phrase = f"{tokens[i]} {tokens[i + 1]}"
                if phrase in self.CONTAINER_PHRASES or (
                    tokens[i] in self.POSITION_WORDS
                    and tokens[i + 1].rstrip("s") in {c.rstrip("s") for c in self.CONTAINER_WORDS}
                ):
                    segment_starts.append(i)
                    i += 2
                    continue

            # Single container word (not at the very start — leave room name)
            word = tokens[i].rstrip("s")
            containers = {c.rstrip("s") for c in self.CONTAINER_WORDS}
            if word in containers and i > 0:
                # If previous token is a position word, start there
                if i > 0 and tokens[i - 1] in self.POSITION_WORDS:
                    if (i - 1) not in segment_starts:
                        segment_starts.append(i - 1)
                else:
                    segment_starts.append(i)
            i += 1

        if not segment_starts:
            # Fallback: first word as place, rest as nested path chunks of ~2 words
            if len(tokens) <= 3:
                return [self._title_case(text)]
            return [
                self._title_case(tokens[0]),
                self._title_case(" ".join(tokens[1:])),
            ]

        segment_starts = sorted(set(segment_starts))
        parts: List[str] = []

        # Leading place name (everything before first container segment)
        first_start = segment_starts[0]
        if first_start > 0:
            parts.append(self._title_case(" ".join(tokens[:first_start])))

        for idx, start in enumerate(segment_starts):
            end = segment_starts[idx + 1] if idx + 1 < len(segment_starts) else len(tokens)
            # Prefer 1–2 word container segments
            chunk = tokens[start:end]
            if len(chunk) > 2 and idx + 1 >= len(segment_starts):
                # Trailing words after last known container — attach carefully
                parts.append(self._title_case(" ".join(chunk[:2])))
                remainder = chunk[2:]
                if remainder:
                    parts.append(self._title_case(" ".join(remainder)))
            else:
                parts.append(self._title_case(" ".join(chunk)))

        return [p for p in parts if p]

    @staticmethod
    def _title_case(text: str) -> str:
        """Title-case while preserving small connector words mid-phrase."""
        small = {"a", "an", "the", "of", "and", "in", "on", "at", "to", "for"}
        words = text.strip().split()
        result = []
        for i, word in enumerate(words):
            lower = word.lower()
            if i > 0 and lower in small:
                result.append(lower)
            else:
                result.append(lower.capitalize())
        return " ".join(result)


def parse_location(text: str) -> List[str]:
    """Module-level helper used across the app."""
    return LocationParser().parse(text)
