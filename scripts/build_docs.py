"""Build the self-contained deliverables: report.html and slides.html at the repo root.

    .venv/bin/python scripts/build_docs.py

Sources live in docs/*.src.html. Tokens replaced at build time:
  {{img:path}}   -> data: URI of that image (so the HTML opens anywhere, screenshots included)
  {{svg:name}}   -> an inline SVG diagram defined below
"""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def box(x, y, w, h, title, sub="", fill="#e8f3f8", stroke="#0f6c8c", dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ""
    lines = [l.strip() for l in sub.split("|")] if sub else []
    block = 16 + 13 * len(lines)                      # title + sub lines, centred vertically
    ty = y + (h - block) / 2 + 8
    t = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>'
         f'<text x="{x + w / 2}" y="{ty}" text-anchor="middle" dominant-baseline="middle" '
         f'font-size="13" font-weight="700" fill="#0b3c50">{title}</text>')
    for i, line in enumerate(lines):
        t += (f'<text x="{x + w / 2}" y="{ty + 17 + 13 * i}" text-anchor="middle" dominant-baseline="middle" '
              f'font-size="10.5" fill="#425466">{line}</text>')
    return t


def arrow(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#5b6675" stroke-width="1.6" marker-end="url(#ah)"/>'


def architecture() -> str:
    llm, code, io = "#e8f3f8", "#f3f0ff", "#f4f6f8"
    parts = ['<svg viewBox="0 0 820 470" xmlns="http://www.w3.org/2000/svg" role="img" '
             'aria-label="Agent architecture" style="width:100%;height:auto;font-family:Helvetica,Arial,sans-serif">',
             '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#5b6675"/></marker></defs>']
    parts.append(box(10, 20, 190, 62, "Learner input", "region · probe · head side · clip", io, "#8a96a5"))
    parts.append(box(10, 110, 190, 62, "De-identify + encrypt", "header mask · EXIF/DICOM strip · AES", code, "#6b4fbb"))
    parts.append(arrow(105, 82, 105, 108))
    parts.append(box(250, 110, 190, 62, "View Router", "LLM, vision: picks the view card", llm))
    parts.append(arrow(200, 141, 248, 141))
    parts.append(box(486, 60, 160, 56, "Identifier", "LLM, vision: view + structures", llm))
    parts.append(box(486, 166, 160, 56, "Quality Grader", "LLM, vision: five 0–2 scores", llm))
    parts.append(arrow(440, 135, 484, 92))
    parts.append(arrow(440, 147, 484, 190))
    parts.append('<text x="565" y="40" text-anchor="middle" font-size="11" fill="#0f6c8c" font-weight="700">Stage 1 · parallel · '
                 '+ view card + reference image</text>')
    parts.append(box(670, 96, 140, 90, "Coordinator", "code: landmark gate | grade = sum | cross-check", code, "#6b4fbb"))
    parts.append(arrow(646, 88, 668, 128))
    parts.append(arrow(646, 194, 668, 156))
    parts.append('<text x="120" y="296" text-anchor="middle" font-size="11" fill="#0f6c8c" font-weight="700">Stage 2 · parallel · text only</text>')
    parts.append('<text x="120" y="312" text-anchor="middle" font-size="10.5" fill="#0f6c8c">(only Probe Guidance if stopped)</text>')
    parts.append(box(250, 280, 170, 56, "Probe Guidance", "LLM: probe moves", llm))
    parts.append(box(440, 280, 170, 56, "Settings Optimizer", "LLM: depth · gain · focus", llm))
    parts.append(box(630, 280, 170, 56, "Findings Tutor", "LLM: cited teaching", llm))
    parts.append(arrow(740, 182, 335, 278))
    parts.append(arrow(740, 182, 525, 278))
    parts.append(arrow(740, 182, 715, 278))
    parts.append(box(250, 380, 360, 62, "Safety Checker (code)", "drops uncited · diagnostic · procedural text", code, "#6b4fbb"))
    parts.append(arrow(335, 336, 380, 378))
    parts.append(arrow(525, 336, 470, 378))
    parts.append(arrow(715, 336, 580, 378))
    parts.append(box(640, 380, 170, 62, "Dashboard verdict", "grade 1–10 · guidance · tokens", io, "#8a96a5"))
    parts.append(arrow(610, 411, 638, 411))
    parts.append(box(10, 380, 200, 62, "Knowledge", "4 view cards · rubric · sources", "#fff7e8", "#a15c00", dash=True))
    parts.append('<text x="10" y="465" font-size="10.5" fill="#5b6675">Blue = gpt-6-luna agents (6) · purple = code · '
                 'dashed = grounding every agent reads</text>')
    parts.append("</svg>")
    return "".join(parts)


SVGS = {"architecture": architecture}


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def build(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8")
    html = re.sub(r"\{\{img:([^}]+)\}\}", lambda m: data_uri(ROOT / m.group(1).strip()), html)
    html = re.sub(r"\{\{svg:([^}]+)\}\}", lambda m: SVGS[m.group(1).strip()](), html)
    left = re.findall(r"\{\{[^}]+\}\}", html)
    if left:
        raise SystemExit(f"{src.name}: unresolved tokens {left}")
    dst.write_text(html, encoding="utf-8")
    print(f"wrote {dst.relative_to(ROOT)} ({dst.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    for name in ("report", "slides"):
        src = DOCS / f"{name}.src.html"
        if src.is_file():
            build(src, ROOT / f"{name}.html")


if __name__ == "__main__":
    main()
