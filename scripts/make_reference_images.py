"""Draw a simulated "ideal" reference image for every view card.

These images are made entirely by this code (no third-party images, figures or schematics), so they can be
committed, shown in the portal and sent to the model (author decision, 2026-11-22). They are teaching
sketches with ultrasound-like texture, not real scans.

Output, for each card id: app/static/reference/<id>.png (plain) and <id>_labeled.png (structures labeled).
Run:  .venv/bin/python scripts/make_reference_images.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "app" / "static" / "reference"

W, H = 640, 480                     # output size
TOP, BOT, LEFT, RIGHT = 40, 456, 70, 570   # image field inside the frame (pixels)
FW, FH = RIGHT - LEFT, BOT - TOP


# ----------------------------------------------------------------------------- texture helpers

def speckle(rng, h=FH, w=FW, sx=5, sy=1.6):
    """Rayleigh speckle, smeared sideways like a real beam."""
    n = rng.rayleigh(1.0, (h, w)).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), sigmaX=sx * 0.35, sigmaY=sy * 0.35)
    return n / n.mean()


class Field:
    """Echo-amplitude map for the image field, in 'cm' coordinates."""

    def __init__(self, depth_cm: float, seed: int):
        self.depth = depth_cm
        self.rng = np.random.default_rng(seed)
        self.amp = np.full((FH, FW), 0.32, np.float32)    # baseline soft-tissue echo
        self.tex = speckle(self.rng)
        self.labels: list[tuple[str, tuple[int, int], tuple[int, int]]] = []
        self.overlay = []                                  # colored drawings (Doppler etc.)

    # coordinates: x in 0..1 across the field, y in cm of depth
    def px(self, x: float, y_cm: float) -> tuple[int, int]:
        return int(x * (FW - 1)), int(y_cm / self.depth * (FH - 1))

    def mask(self) -> np.ndarray:
        return np.zeros((FH, FW), np.float32)

    def band(self, y0, y1, level, x0=0.0, x1=1.0):
        m = self.mask()
        a, b = self.px(x0, y0), self.px(x1, y1)
        m[a[1]:b[1], a[0]:b[0]] = 1
        m = cv2.GaussianBlur(m, (0, 0), 2)
        self.amp = self.amp * (1 - m) + level * m

    def ellipse(self, x, y, rx, ry, level, angle=0, soft=2.0):
        m = self.mask()
        c = self.px(x, y)
        cv2.ellipse(m, c, (max(1, int(rx * FW)), max(1, int(ry / self.depth * FH))), angle, 0, 360, 1, -1)
        if soft:
            m = cv2.GaussianBlur(m, (0, 0), soft)
        self.amp = self.amp * (1 - m) + level * m
        return m

    def poly_fill(self, pts, level, soft=2.0):
        m = self.mask()
        cv2.fillPoly(m, [np.array([self.px(x, y) for x, y in pts], np.int32)], 1)
        if soft:
            m = cv2.GaussianBlur(m, (0, 0), soft)
        self.amp = self.amp * (1 - m) + level * m
        return m

    def line(self, pts, level, thick=3, blur=1.2):
        m = self.mask()
        cv2.polylines(m, [np.array([self.px(x, y) for x, y in pts], np.int32)], False, 1, thick, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), blur)
        self.amp = np.maximum(self.amp, level * m)

    def arc(self, x, y, rx, ry, a0, a1, level, thick=3):
        m = self.mask()
        cv2.ellipse(m, self.px(x, y), (int(rx * FW), int(ry / self.depth * FH)), 0, a0, a1, 1, thick, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 1.2)
        self.amp = np.maximum(self.amp, level * m)

    def shadow(self, x0, x1, y_from, strength=0.9, edge=4):
        """Acoustic shadow straight down below a strong reflector."""
        m = self.mask()
        a, b = self.px(x0, y_from), self.px(x1, self.depth)
        m[a[1]:, a[0]:b[0]] = 1
        m = cv2.GaussianBlur(m, (0, 0), edge)
        self.amp *= (1 - strength * m)

    def reverberations(self, pts_fn, first_y, spacing, n, level, x0, x1, decay=0.7, thick=3):
        """Repeating copies of a bright air line (A-line style)."""
        for k in range(1, n + 1):
            y = first_y + k * spacing
            if y >= self.depth:
                break
            pts = [(x, pts_fn(x) + k * spacing) for x in np.linspace(x0, x1, 40)]
            self.line(pts, level * decay ** (k - 1), thick=thick, blur=2.0)

    def label(self, text, at, text_pos):
        """at / text_pos as (x 0..1, y cm)."""
        self.labels.append((text, self.px(*at), self.px(*text_pos)))

    def render(self, gain=1.0, tgc=0.12):
        y = np.linspace(0, 1, FH, dtype=np.float32)[:, None]
        att = np.exp(-tgc * y * self.depth)                 # depth attenuation
        img = self.amp * self.tex * att * gain
        img = np.log1p(6 * img) / np.log1p(6 * 1.6)        # log compression
        return np.clip(img * 255, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- framing and labels

def frame(gray_field: np.ndarray, f: Field, title: str, *, sector=False, color_layers=None) -> np.ndarray:
    canvas = np.zeros((H, W, 3), np.uint8)
    field = cv2.cvtColor(gray_field, cv2.COLOR_GRAY2BGR)
    if color_layers is not None:
        for (m, bgr) in color_layers:
            for c in range(3):
                field[..., c] = (field[..., c] * (1 - m) + bgr[c] * m).astype(np.uint8)
    if sector:
        mask = np.zeros((FH, FW), np.uint8)
        apex = (FW // 2, -int(FH * 0.35))
        r_in, r_out = int(FH * 0.38), int(FH * 1.33)
        cv2.ellipse(mask, apex, (r_out, r_out), 90, -33, 33, 255, -1)
        cv2.ellipse(mask, apex, (r_in, r_in), 90, -33, 33, 0, -1)
        field[mask == 0] = 0
    canvas[TOP:BOT, LEFT:RIGHT] = field
    # depth scale (cm) on the right
    for cm in range(0, int(f.depth) + 1):
        yy = TOP + int(cm / f.depth * (FH - 1))
        cv2.line(canvas, (RIGHT + 6, yy), (RIGHT + 14, yy), (200, 200, 200), 1)
        cv2.putText(canvas, str(cm), (RIGHT + 18, yy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1,
                    cv2.LINE_AA)
    cv2.putText(canvas, "cm", (RIGHT + 16, BOT + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1, cv2.LINE_AA)
    # probe-marker indicator: marker side of the screen is the left
    cv2.circle(canvas, (LEFT + 8, TOP - 12), 5, (90, 200, 255), -1)
    cv2.putText(canvas, title, (LEFT + 22, TOP - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.putText(canvas, "SIMULATED REFERENCE - drawn by code, not a patient image", (LEFT, H - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (150, 150, 150), 1, cv2.LINE_AA)
    return canvas


def add_labels(img: np.ndarray, f: Field) -> np.ndarray:
    out = img.copy()
    col = (60, 230, 255)    # yellow-ish (BGR)
    for text, at, tp in f.labels:
        a = (at[0] + LEFT, at[1] + TOP)
        t = (tp[0] + LEFT, tp[1] + TOP)
        cv2.line(out, a, t, col, 1, cv2.LINE_AA)
        cv2.circle(out, a, 3, col, -1, cv2.LINE_AA)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        tx = min(max(t[0] - tw // 2, 2), W - tw - 2)
        ty = t[1] - 4 if t[1] < a[1] else t[1] + th + 4
        cv2.rectangle(out, (tx - 3, ty - th - 3), (tx + tw + 3, ty + 4), (0, 0, 0), -1)
        cv2.putText(out, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, 1, cv2.LINE_AA)
    return out


def soft_tissue_layers(f: Field, skin=0.15, sub=0.45, muscle_to=None):
    f.band(0, skin, 0.75)                                   # skin: bright
    f.band(skin, sub, 0.22)                                 # subcutaneous fat: darker
    if muscle_to:
        f.band(sub, muscle_to, 0.42)                        # muscle: medium, striated
        for yy in np.linspace(sub + 0.08, muscle_to - 0.05, 4):
            f.line([(x, yy + 0.02 * np.sin(6 * x)) for x in np.linspace(0, 1, 30)], 0.55, thick=1, blur=1.0)


# ----------------------------------------------------------------------------- the nine views

def v01_bat_sign():
    f = Field(5.0, 1)
    soft_tissue_layers(f, muscle_to=1.3)
    ry = 1.45
    for xc in (0.16, 0.84):                                # two ribs: bright arc + full shadow
        f.arc(xc, ry + 0.35, 0.11, 0.35, 180, 360, 1.0, thick=4)
        f.shadow(xc - 0.11, xc + 0.11, ry + 0.05, strength=0.93)
    py = 1.95                                              # pleural line, ~0.5 cm deeper than rib line
    f.line([(x, py) for x in np.linspace(0.27, 0.73, 30)], 1.15, thick=4)
    f.band(py + 0.08, 5.0, 0.20, 0.27, 0.73)               # air-filled lung: low, grainy echo
    f.reverberations(lambda x: py, py, py, 2, 0.65, 0.29, 0.71, decay=0.65, thick=3)
    f.label("Rib + shadow", (0.16, 1.5), (0.16, 0.5))
    f.label("Rib + shadow", (0.84, 1.5), (0.84, 0.5))
    f.label("Pleural line", (0.5, py), (0.5, 1.05))
    f.label("A-line", (0.5, 2 * py), (0.5, 3.35))
    return f, "01 Anterior pleura, longitudinal (bat sign)", {}


def v02_intercostal():
    f = Field(7.0, 2)
    soft_tissue_layers(f, muscle_to=1.2)
    py = 1.6
    f.line([(x, py + 0.03 * np.sin(4 * x)) for x in np.linspace(0, 1, 50)], 1.15, thick=4)
    f.band(py + 0.1, 7.0, 0.2)
    f.reverberations(lambda x: py, py, py, 3, 0.6, 0.0, 0.55, decay=0.65)
    # one B-line: bright, sharp, from the pleura to the bottom, erasing A-lines it crosses
    x0 = 0.72
    m = f.mask()
    a, b = f.px(x0 - 0.012, py), f.px(x0 + 0.012, 7.0)
    m[a[1]:, a[0]:b[0]] = 1
    m = cv2.GaussianBlur(m, (0, 0), 2.5)
    f.amp = f.amp * (1 - m) + 0.95 * m
    f.reverberations(lambda x: py, py, py, 3, 0.6, 0.62, 1.0, decay=0.65)
    # Z-line for contrast: short, fades early
    zx = 0.88
    zm = f.mask()
    za, zb = f.px(zx - 0.008, py), f.px(zx + 0.008, py + 0.9)
    zm[za[1]:zb[1], za[0]:zb[0]] = np.linspace(1, 0, zb[1] - za[1])[:, None]
    zm = cv2.GaussianBlur(zm, (0, 0), 1.5)
    f.amp = np.maximum(f.amp, 0.7 * zm)
    f.label("Continuous pleural line (no rib shadows)", (0.3, py), (0.3, 0.55))
    f.label("A-line", (0.25, 2 * py), (0.25, 4.0))
    f.label("B-line: reaches the bottom", (x0, 5.5), (0.5, 6.4))
    f.label("Z-line: short, fades", (zx, py + 0.5), (0.86, 3.2))
    return f, "02 Intercostal view: A-lines, one B-line", {}


def v03_mmode():
    """Top: small B-mode reference with the cursor. Bottom: M-mode seashore trace."""
    f = Field(5.0, 3)
    rng = f.rng
    half = FH // 2
    # --- top half: compressed bat sign
    top = Field(5.0, 33)
    soft_tissue_layers(top, muscle_to=1.3)
    for xc in (0.16, 0.84):
        top.arc(xc, 1.8, 0.11, 0.35, 180, 360, 1.0, thick=4)
        top.shadow(xc - 0.11, xc + 0.11, 1.5, strength=0.93)
    top.line([(x, 1.95) for x in np.linspace(0.27, 0.73, 30)], 1.15, thick=4)
    top.band(2.05, 5.0, 0.2, 0.27, 0.73)
    top_img = cv2.resize(top.render(), (FW, half))
    # --- bottom half: M-mode, time across, depth down
    py = int(1.95 / 5.0 * half)
    tex_above = np.repeat(rng.rayleigh(1, (half, 1)).astype(np.float32), FW, axis=1)   # steady horizontal lines
    tex_above = cv2.GaussianBlur(tex_above, (0, 0), sigmaX=1, sigmaY=0.8)
    sand = rng.rayleigh(1, (half, FW)).astype(np.float32)
    sand = cv2.GaussianBlur(sand, (0, 0), sigmaX=1.2, sigmaY=1.2)                        # granular "sand"
    mm = np.where(np.arange(half)[:, None] < py, 0.45 * tex_above, 0.32 * sand)
    mm[:int(0.15 / 5 * half)] = 0.8 * tex_above[:int(0.15 / 5 * half)]
    mm[py - 2:py + 3] = 1.25
    mm *= np.exp(-0.12 * np.linspace(0, 5, half, dtype=np.float32))[:, None]
    mm_img = np.clip(np.log1p(6 * mm) / np.log1p(6 * 1.6) * 255, 0, 255).astype(np.uint8)
    img = np.vstack([top_img, mm_img[:FH - half]])
    # cursor (dotted) through the pleura between the ribs, on the B-mode part
    cx = FW // 2
    for yy in range(0, half, 8):
        cv2.line(img, (cx, yy), (cx, yy + 4), 230, 1)
    cv2.line(img, (0, half), (FW, half), 120, 1)
    f.labels = [
        ("M-mode cursor between the ribs", (cx, int(half * 0.6)), (int(FW * 0.5), int(half * 0.12))),
        ("Pleural line", (int(FW * 0.15), half + py), (int(FW * 0.15), half + py - 34)),
        ("Still chest wall: horizontal lines", (int(FW * 0.75), half + py // 2), (int(FW * 0.72), half + 8)),
        ("Seashore: grainy 'sand' below the pleura", (int(FW * 0.6), half + py + 50), (int(FW * 0.55), FH - 30)),
    ]
    f._prerendered = img
    return f, "03 M-mode through the pleura (seashore sign)", {}


def v04_plaps():
    """Coronal costophrenic view, marker (head) on the left. The diaphragm is a bright dome, convex toward the
    lung and concave over the liver: the liver sits UNDER the dome (author correction, 2026-11-23)."""
    f = Field(15.0, 4)
    f.band(0, 0.3, 0.7)                                     # skin
    f.band(0.3, 1.5, 0.28)                                  # subcutaneous fat
    f.band(1.5, 2.6, 0.45)                                  # intercostal muscle
    cx, cy, rx, ry = 0.88, 13.2, 0.62, 9.0                  # dome = upper-left quarter of this ellipse
    ys, xs = np.mgrid[0:FH, 0:FW].astype(np.float32)
    xn, ycm = xs / (FW - 1), ys / (FH - 1) * f.depth
    inside = ((((xn - cx) / rx) ** 2 + ((ycm - cy) / ry) ** 2) <= 1.0).astype(np.float32)
    body = (ycm > 2.7).astype(np.float32)
    liver = cv2.GaussianBlur(inside * body, (0, 0), 2.5)
    lung = cv2.GaussianBlur((1 - inside) * body, (0, 0), 2.5)
    # Liver: medium, homogeneous, fine even texture, a little brighter than muscle.
    # Aerated lung above the dome: mirror image of the liver, dimmer and coarser/blurred.
    f.amp = f.amp * (1 - liver - lung) + 0.46 * liver + 0.37 * lung
    fine = cv2.GaussianBlur(speckle(f.rng, sx=3, sy=3), (0, 0), 0.9)
    coarse = cv2.GaussianBlur(speckle(f.rng, sx=3, sy=3), (0, 0), 1.6)   # mirror image: liver-like, hazier
    f.tex = f.tex * (1 - liver - lung) + fine * liver + coarse * lung
    # a few portal-vein-like dark tubes with bright walls inside the liver
    for (vx, vy, vr) in [(0.72, 8.0, 0.025), (0.62, 10.6, 0.02), (0.85, 11.2, 0.03)]:
        f.ellipse(vx, vy, vr, vr * 15 * 0.7, 0.08, soft=1.2)
    f.arc(cx, cy, rx, ry, 180, 272, 1.7, thick=8)          # bright (hyperechoic) diaphragm
    for x in np.linspace(0.62, 0.92, 4):                    # spine: deep, only on the liver side of the dome
        f.line([(x - 0.03, 13.7), (x + 0.03, 13.7)], 1.0, thick=4)
        f.shadow(x - 0.03, x + 0.03, 13.9, 0.85, edge=2)
    ang = np.deg2rad(222)
    dxp, dyp = cx + rx * np.cos(ang), cy + ry * np.sin(ang)
    f.label("Chest wall", (0.62, 1.6), (0.8, 1.6))
    f.label("Diaphragm: bright dome, concave over the liver", (dxp, dyp), (0.5, 4.0))
    f.label("Liver (under the diaphragm)", (0.78, 9.5), (0.82, 7.0))
    f.label("Lung above the diaphragm (mirror image)", (0.2, 7.5), (0.26, 11.8))
    f.label("Space above the diaphragm: no fluid", (dxp - 0.06, dyp - 0.4), (0.22, 3.3))
    f.label("Spine stops at the diaphragm", (0.8, 13.7), (0.72, 14.5))
    return f, "04 Posterolateral / PLAPS (curvilinear, head on the left)", {"sector": True}


VIEWS = {
    "anterior_pleura_longitudinal": v01_bat_sign,
    "intercostal_aeration": v02_intercostal,
    "mmode_pleura": v03_mmode,
    "posterolateral_plaps": v04_plaps,
}


def build(view_id: str) -> tuple[np.ndarray, np.ndarray]:
    f, title, opts = VIEWS[view_id]()
    gray = getattr(f, "_prerendered", None)
    if gray is None:
        gray = f.render()
    color = opts.get("color")
    img = frame(gray, f, title, sector=opts.get("sector", False), color_layers=color)
    if hasattr(f, "_box"):
        (a, b) = f._box
        cv2.rectangle(img, (a[0] + LEFT, a[1] + TOP), (b[0] + LEFT, b[1] + TOP), (200, 200, 200), 1)
    return img, add_labels(img, f)


def main() -> None:
    from app.coach.cards import load_cards
    OUT.mkdir(parents=True, exist_ok=True)
    missing = set(load_cards()) - set(VIEWS)
    if missing:
        raise SystemExit(f"No reference drawing for: {sorted(missing)}")
    for vid in VIEWS:
        plain, labeled = build(vid)
        cv2.imwrite(str(OUT / f"{vid}.png"), plain)
        cv2.imwrite(str(OUT / f"{vid}_labeled.png"), labeled)
        print("wrote", vid)


if __name__ == "__main__":
    main()
