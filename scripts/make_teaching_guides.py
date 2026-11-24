"""Build human-readable PDF teaching guides from the view cards.

One PDF per card (with its simulated reference image, labeled and plain), one for the grading rubric, and one
combined file. Output: "Ultrasound teaching guides/". Uses headless Google Chrome to print HTML to PDF.

Run:  .venv/bin/python scripts/make_teaching_guides.py
"""

from __future__ import annotations

import base64
import html
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CARDS = ROOT / "knowledge" / "view_cards"
REF = ROOT / "app" / "static" / "reference"
OUT = ROOT / "Ultrasound teaching guides"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SHORT = {"01": "Anterior pleura - bat sign", "02": "Intercostal view - A and B lines",
         "03": "M-mode of the pleura", "04": "Posterolateral PLAPS view"}
REGION_NAMES = {"anterior": "Anterior chest", "lateral": "Lateral chest"}


def regions_of(meta: dict) -> str:
    return " / ".join(REGION_NAMES.get(r.strip(), r.strip()) for r in meta.get("regions", "anterior").strip("[]").split(","))


# ----------------------------------------------------------------------------- tiny markdown to HTML

def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"~~(.+?)~~", r"<del>\1</del>", s)
    s = re.sub(r"(\[(?:[A-Za-z]+\d{2}|AUTH)\b[^\]]*\])", r'<span class="cite">\1</span>', s)
    return s


def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    stack: list[tuple[int, str]] = []          # open lists: (indent, tag)

    def close_lists(to_indent=-1):
        while stack and stack[-1][0] > to_indent:
            out.append(f"</li></{stack.pop()[1]}>")

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            close_lists(); i += 1
            continue
        if line.startswith("|"):                   # table
            close_lists()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(set(c) <= set("-: ") for c in r)]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>")
            out += ["<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body]
            out.append("</tbody></table>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            close_lists()
            lvl = len(m.group(1)) + 1
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if line.startswith(">"):
            close_lists()
            out.append(f"<blockquote>{inline(line.lstrip('> ').strip())}</blockquote>")
            i += 1
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", line)
        if m:
            indent, marker, text = len(m.group(1)), m.group(2), m.group(3)
            tag = "ol" if marker[0].isdigit() else "ul"
            if stack and stack[-1][0] == indent and stack[-1][1] == tag:
                out.append(f"</li><li>{inline(text)}")
            elif stack and stack[-1][0] >= indent:
                close_lists(indent)
                if stack and stack[-1][0] == indent:
                    out.append(f"</li><li>{inline(text)}")
                else:
                    stack.append((indent, tag)); out.append(f"<{tag}><li>{inline(text)}")
            else:
                stack.append((indent, tag)); out.append(f"<{tag}><li>{inline(text)}")
            i += 1
            continue
        close_lists()
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\s*([-*]|\d+\.)\s|#|\||>)", lines[i]):
            para.append(lines[i].strip()); i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    close_lists()
    return "\n".join(out)


# ----------------------------------------------------------------------------- pieces

def front_matter(text: str) -> tuple[dict, str]:
    meta = {}
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for ln in fm.strip().splitlines():
            k, _, v = ln.partition(":")
            meta[k.strip()] = v.strip()
        return meta, body
    return meta, text


def sources_table() -> dict[str, str]:
    rows = {}
    for ln in (ROOT / "knowledge" / "sources.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([A-Za-z]+\d{2}|AUTH)\s*\|\s*(.+?)\s*\|", ln)
        if m:
            rows[m.group(1)] = m.group(2)
    return rows


def img_tag(path: Path, cls: str, alt: str) -> str:
    if not path.is_file():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f'<img class="{cls}" alt="{html.escape(alt)}" src="data:image/png;base64,{b64}">'


CSS = """
@page { size: Letter; margin: 16mm 15mm 18mm; }
* { box-sizing: border-box; }
body { font: 10.5pt/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #1d2430; margin: 0; }
.banner { background: #0f2533; color: #fff; padding: 14px 18px; border-radius: 8px; margin-bottom: 14px; }
.banner .num { font-size: 10pt; letter-spacing: .08em; text-transform: uppercase; color: #7fd3ff; }
.banner h1 { font-size: 17pt; margin: 2px 0 6px; line-height: 1.2; }
.banner .meta { font-size: 9pt; color: #c9d7e3; }
.tag { display: inline-block; padding: 1px 8px; border-radius: 999px; background: #1f4b66; margin-right: 6px; }
.tag.draft { background: #7a5a12; }
h2 { font-size: 13pt; color: #0f3d57; border-bottom: 2px solid #d6e6f0; padding-bottom: 3px; margin: 18px 0 8px; page-break-after: avoid; }
h3 { font-size: 11pt; color: #0f3d57; margin: 12px 0 6px; }
p { margin: 6px 0; }
ul, ol { margin: 4px 0 8px; padding-left: 20px; }
li { margin: 2px 0; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 12px; font-size: 9.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #eaf3f8; text-align: left; color: #0f3d57; }
th, td { border: 1px solid #cfdde6; padding: 5px 7px; vertical-align: top; }
blockquote { margin: 8px 0; padding: 6px 10px; background: #f3f7fa; border-left: 3px solid #7fb7d3; font-size: 9.5pt; }
code { background: #eef2f5; padding: 0 3px; border-radius: 3px; font-size: 9pt; }
.cite { color: #6b7d8c; font-size: 8pt; white-space: nowrap; }
.figure { page-break-inside: avoid; margin: 4px 0 10px; }
.figure .main { width: 100%; border-radius: 6px; display: block; }
.figure .row { display: flex; gap: 10px; align-items: flex-start; margin-top: 8px; }
.figure .plain { width: 48%; border-radius: 6px; }
.figure .caption { font-size: 8.5pt; color: #4b5b68; }
.sources { font-size: 8.5pt; color: #3c4b57; }
.sources li { margin: 3px 0; }
.foot { margin-top: 16px; font-size: 8pt; color: #6b7d8c; border-top: 1px solid #d6e6f0; padding-top: 6px; }
.break { page-break-before: always; }
.toc td:first-child { width: 42px; font-weight: 700; color: #0f3d57; }
"""


def card_html(path: Path, srcs: dict[str, str]) -> tuple[str, str, str]:
    num = path.name[:2]
    meta, body = front_matter(path.read_text(encoding="utf-8"))
    vid = meta.get("id", "")
    region = regions_of(meta)
    status = meta.get("status", "")
    labeled = img_tag(REF / f"{vid}_labeled.png", "main", f"Labeled simulated reference for card {num}")
    plain = img_tag(REF / f"{vid}.png", "plain", f"Unlabeled simulated reference for card {num}")
    figure = ""
    if labeled:
        figure = f"""<h2>Reference image (what a good image looks like)</h2>
<div class="figure">{labeled}
<div class="row">{plain}<div class="caption"><strong>Left:</strong> the same view without labels, to practice
recognizing the structures yourself.<br><br>These are <strong>simulated teaching drawings made by our own code</strong>,
not patient images. By convention the probe marker and the patient's head are on the <strong>left</strong> of the
screen on longitudinal views (patient's right on transverse views); some machines show the mirror image.</div></div></div>"""
    keys = sorted(set(re.findall(r"\[([A-Za-z]+\d{2})\b", body)))
    src_html = "".join(f"<li><strong>{k}</strong>: {inline(srcs.get(k, 'see knowledge/sources.md'))}</li>" for k in keys)
    content = f"""<div class="banner"><div class="num">Card {num} · {region}</div>
<h1>{html.escape(meta.get('name', path.stem))}</h1>
<div class="meta"><span class="tag">{html.escape(meta.get('modes', '').strip('[]'))}</span>
<span class="tag{' draft' if 'DRAFT' in status else ''}">{html.escape(status or 'approved')}</span></div></div>
{figure}
{md_to_html(body)}
<h2>Sources cited on this card</h2><ul class="sources">{src_html}</ul>
<div class="foot">POCUS Lung Coach · teaching guide generated {date.today().isoformat()} from
<code>knowledge/view_cards/{path.name}</code>. Concepts are paraphrased from the cited sources; no third-party
images are used. Educational use only. Not for diagnosis or patient care decisions.</div>"""
    title = f"{num} {SHORT.get(num, meta.get('name', path.stem))}"
    return title, content, vid


def page(title: str, body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>{CSS}</style></head><body>{body}</body></html>"


def to_pdf(html_text: str, pdf: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "page.html"
        src.write_text(html_text, encoding="utf-8")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", src.as_uri()], check=True, capture_output=True, timeout=120)


def main() -> None:
    if not Path(CHROME).exists():
        raise SystemExit("Google Chrome is needed to print the PDFs.")
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.pdf"):
        old.unlink()
    srcs = sources_table()
    parts, toc = [], []
    for path in sorted(CARDS.glob("[0-9][0-9]_*.md")):
        title, content, vid = card_html(path, srcs)
        to_pdf(page(title, content), OUT / f"{title}.pdf")
        parts.append(content)
        toc.append((path.name[:2], front_matter(path.read_text(encoding="utf-8"))[0].get("name", ""),
                    regions_of(front_matter(path.read_text(encoding="utf-8"))[0])))
        print("wrote", f"{title}.pdf")
    _, rubric = front_matter((CARDS / "grading_rubric.md").read_text(encoding="utf-8"))
    rubric_html = f"""<div class="banner"><div class="num">Grading</div><h1>Image quality grading rubric (1–10)</h1>
<div class="meta">Used by the Quality Grader and by the author when labeling pilot images.</div></div>{md_to_html(rubric)}"""
    to_pdf(page("00 Grading rubric", rubric_html), OUT / "00 Grading rubric.pdf")
    print("wrote 00 Grading rubric.pdf")
    toc_rows = "".join(f"<tr><td>{n}</td><td>{html.escape(name)}</td><td>{r}</td></tr>" for n, name, r in toc)
    cover = f"""<div class="banner"><div class="num">POCUS Lung Coach</div>
<h1>Ultrasound teaching guides</h1><div class="meta">The four lung view cards the AI coach is grounded in, with their
simulated reference images, plus the grading rubric. Generated {date.today().isoformat()}.</div></div>
<table class="toc"><thead><tr><th>Card</th><th>View</th><th>Region</th></tr></thead><tbody>{toc_rows}
<tr><td>–</td><td>Image quality grading rubric (1–10)</td><td>All</td></tr></tbody></table>
<p class="foot">Educational use only. Not for diagnosis or patient care decisions.</p>"""
    combined = cover + "".join(f'<div class="break"></div>{p}' for p in parts) + f'<div class="break"></div>{rubric_html}'
    to_pdf(page("All teaching guides", combined), OUT / "All teaching guides (combined).pdf")
    print("wrote All teaching guides (combined).pdf")


if __name__ == "__main__":
    main()
