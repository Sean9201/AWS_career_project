"""Canonical skill dictionary. Extraction and verification share the same matching rules."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Match:
    skill: str
    text: str
    start: int
    end: int


class SkillDictionary:
    def __init__(self, entries):
        self.entries = {k: v for k, v in entries.items() if not k.startswith('_')}
        names = [(alias, canon) for canon, entry in self.entries.items()
                 for alias in (canon, *entry.get('aliases', []))]
        self._lookup = {alias.casefold(): canon for alias, canon in names}
        # Longest alias first, so "Spring Boot" wins over "Spring" and "JavaScript" over "Java".
        names.sort(key=lambda pair: -len(pair[0]))
        # ASCII-only boundaries: Korean particles may follow ("Python을") but "Java" in "JavaScript" may not.
        self._patterns = [(re.compile(rf'(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9+#])', re.IGNORECASE), canon)
                          for alias, canon in names]

    @classmethod
    def load(cls, path=ROOT / 'data' / 'skills.json'):
        return cls(json.loads(Path(path).read_text(encoding='utf-8')))

    def find(self, text):
        """Non-overlapping dictionary matches in text order."""
        taken, found = [], []
        for pattern, canon in self._patterns:
            for m in pattern.finditer(text):
                if any(m.start() < end and start < m.end() for start, end in taken):
                    continue
                taken.append((m.start(), m.end()))
                found.append(Match(canon, m.group(0), m.start(), m.end()))
        return sorted(found, key=lambda m: m.start)

    def canonical(self, name):
        """Map a free-form skill name to its canonical name, or None if it is unknown or ambiguous."""
        name = (name or '').strip()
        if name.casefold() in self._lookup:
            return self._lookup[name.casefold()]
        matched = {m.skill for m in self.find(name)}
        return matched.pop() if len(matched) == 1 else None

    def names(self):
        return sorted(self.entries)
