"""Scope, search and reading for the house wiki. No Home Assistant imports, so it can be tested alone.

Pages are markdown files from a git repo. A page is in scope when its path starts with an included prefix, or when it
sits under a "mention" prefix and its text names one of the mention terms; any path containing an excluded string is
left out. Search is plain keyword scoring with the title weighted up, which is enough for a few hundred notes.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

STOP = set(
    "a an and are as at be by did do does for from had has have how i in is it its me my of on or our the their "
    "there this to was we what when where which who why will with you your".split()
)
READ_LIMIT = 6000
SNIPPET = 280


@dataclass(frozen=True)
class Page:
    path: str
    title: str
    text: str


@dataclass(frozen=True)
class Scope:
    include: tuple[str, ...]
    mention_in: tuple[str, ...]
    mention_terms: tuple[str, ...]
    exclude: tuple[str, ...]

    def candidate(self, path: str) -> bool:
        """Worth downloading: a markdown file under an included or mention prefix, not excluded."""
        return (
            path.endswith(".md")
            and any(path.startswith(p) for p in self.include + self.mention_in)
            and not self.excluded(path)
        )

    def excluded(self, path: str) -> bool:
        return any(x and x in path for x in self.exclude)

    def keeps(self, path: str, text: str) -> bool:
        if not self.candidate(path):
            return False
        if any(path.startswith(p) for p in self.include):
            return True
        low = text.lower()
        return any(t and t.lower() in low for t in self.mention_terms)


def split_list(value: str | list[str] | None) -> tuple[str, ...]:
    """Options are typed as text, one entry per line or comma separated."""
    if not value:
        return ()
    items = value if isinstance(value, list) else re.split(r"[\n,]", value)
    return tuple(s.strip() for s in items if s.strip())


def make_page(path: str, raw: str) -> Page:
    """Drop YAML front matter; the title is its `title:` or else the file name."""
    text = raw.replace("\r\n", "\n")
    title = path.rsplit("/", 1)[-1].removesuffix(".md")
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            front = text[4:end]
            m = re.search(r"^title:\s*(.+)$", front, re.M)
            if m:
                title = m.group(1).strip().strip("\"'")
            text = text[end + 4 :].lstrip("\n")
    return Page(path, title, text)


def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def _stem(w: str) -> str:
    """Rough plural/verb folding so 'filters' finds 'filter' and 'changed' finds 'change'."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(w) > len(suffix) + 2 and w.endswith(suffix):
            return w[: -len(suffix)]
    return w


def _terms(query: str) -> list[str]:
    return list(dict.fromkeys(_stem(w) for w in words(query)))


def _hits(terms: list[str], text: str) -> int:
    stems = [_stem(w) for w in words(text)]
    return sum(min(stems.count(t), 5) for t in terms)


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n|\n(?=#)", text) if p.strip()]


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def search(pages: list[Page], query: str, limit: int = 5) -> list[dict[str, object]]:
    """Best pages for the query, each with its two best-matching paragraphs."""
    terms = _terms(query)
    if not terms:
        return []
    scored = []
    for page in pages:
        title_hits = sum(1 for t in terms if t in [_stem(w) for w in words(page.title)])
        body = _hits(terms, page.text)
        covered = sum(1 for t in terms if t in {_stem(w) for w in words(page.title + " " + page.text)})
        if not body and not title_hits:
            continue
        scored.append((title_hits * 6 + body + covered * 4, page))
    scored.sort(key=lambda s: -s[0])
    out = []
    for _, page in scored[:limit]:
        paras = sorted(_paragraphs(page.text), key=lambda p: -_hits(terms, p))
        out.append(
            {
                "page": page.title,
                "path": page.path,
                "snippets": [_clip(p, SNIPPET) for p in paras[:2] if _hits(terms, p)],
            }
        )
    return out


def _sections(text: str) -> list[str]:
    parts = re.split(r"\n(?=#{1,4} )", "\n" + text)
    return [p.strip() for p in parts if p.strip()]


def find_page(pages: list[Page], name: str) -> Page | None:
    """By exact path, then exact title, then the title containing the name (shortest wins)."""
    want = name.strip().lower().removesuffix(".md")
    for page in pages:
        if page.path.lower().removesuffix(".md") == want or page.title.lower() == want:
            return page
    hits = [p for p in pages if want in p.title.lower() or want in p.path.lower()]
    return min(hits, key=lambda p: len(p.title)) if hits else None


def read(pages: list[Page], name: str, find: str | None = None) -> dict[str, object]:
    """A page's text. Long pages (like a log) return only the sections matching `find`, or the start."""
    page = find_page(pages, name)
    if page is None:
        return {"error": f"No page called '{name}'. Search first to get the page name."}
    text = page.text
    if find:
        terms = _terms(find)
        matching = [s for s in _sections(text) if _hits(terms, s)]
        matching.sort(key=lambda s: -_hits(terms, s))
        text = "\n\n".join(matching) if matching else ""
        if not text:
            return {"page": page.title, "path": page.path, "text": "", "note": f"Nothing on this page matches '{find}'."}
    truncated = len(text) > READ_LIMIT
    result: dict[str, object] = {"page": page.title, "path": page.path, "text": text[:READ_LIMIT]}
    if truncated:
        result["note"] = "Cut short. Call again with `find` to get only the sections you need."
    return result
