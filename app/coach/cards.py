"""Load the view cards (knowledge/view_cards/*.md) into structured form for the UI and the agents."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from app import settings

CITE = re.compile(r"\s*(\[[A-Za-z]+\d{2}[^\]]*\])+")


@dataclass
class ViewCard:
    id: str
    name: str
    status: str
    modes: list[str]
    text: str                                   # full markdown, for the agents
    must_see: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)   # (what you see, coach says)
    settings: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=lambda: ["anterior"])   # chest regions this view belongs to

    @property
    def region(self) -> str:
        return self.regions[0]


def strip_cites(s: str) -> str:
    return CITE.sub("", s).strip()


def short_label(item: str, limit: int = 60) -> str:
    """Short checklist label: the bold lead-in if there is one, else the first clause."""
    m = re.match(r"\*\*(.+?)\*\*", item)
    if m:
        return m.group(1).rstrip(":. ")
    text = re.split(r"\s\(|;|\.\s", item)[0].rstrip(".")
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def plain(item: str) -> str:
    return re.sub(r"\*\*(.*?)\*\*", r"\1", item)


def _section(md: str, title_start: str) -> str:
    m = re.search(rf"^## {re.escape(title_start)}.*?$(.*?)(?=^## |\Z)", md, re.M | re.S)
    return m.group(1) if m else ""


def _parse(path) -> ViewCard | None:
    md = path.read_text(encoding="utf-8")
    fm = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if not fm:
        return None
    meta = dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M))
    card = ViewCard(id=meta["id"], name=meta["name"], status=meta.get("status", ""),
                    modes=[m.strip() for m in meta.get("modes", "").strip("[]").split(",") if m.strip()],
                    text=md,
                    regions=[r.strip() for r in meta.get("regions", "anterior").strip("[]").split(",") if r.strip()])
    for line in _section(md, "Target image").splitlines():
        m = re.match(r"^\s*(?:\d+\.|-)\s+(.*)", line)
        if m:
            card.must_see.append(strip_cites(m.group(1)))
    for line in _section(md, "Common errors").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and not set(cells[0]) <= set("-: ") and cells[0] not in ("What you see",):
            card.errors.append((strip_cites(cells[0]), strip_cites(cells[-1]).strip('"')))
    for line in _section(md, "Recommended settings").splitlines():
        m = re.match(r"^\s*-\s+(.*)", line)
        if m:
            card.settings.append(re.sub(r"\*\*(.*?)\*\*", r"\1", strip_cites(m.group(1))))
    return card


@lru_cache(maxsize=1)
def load_cards() -> dict[str, ViewCard]:
    cards = {}
    for p in sorted(settings.KNOWLEDGE_DIR.glob("[0-9][0-9]_*.md")):
        c = _parse(p)
        if c:
            cards[c.id] = c
    return cards


def rubric_text() -> str:
    return (settings.KNOWLEDGE_DIR / "grading_rubric.md").read_text(encoding="utf-8")
