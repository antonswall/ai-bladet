#!/usr/bin/env python3
"""
AI-Bladet — Grafisk fallback (Pipeline Steg 5, nivå 4)
=======================================================
Genererar snygga SVG-placeholders i tidningens formspråk när ingen
riktig bild hittas (OG / AI-genererad / Openverse / bildbank).

En SVG per kategori skrivs till static/img/fallback/ och byggs med i
sajten via build.js (static → public). URL:erna är absoluta så att de
även fungerar som og:image.

Användning:
    import fallback_image
    url, credit = fallback_image.get("Modeller")

    python fallback_image.py   # regenerera alla SVG:er
"""

import re
import unicodedata
from pathlib import Path

SITE_URL = "https://aibladet.se"
STATIC_IMG_DIR = Path(__file__).parent.parent / "static" / "img" / "fallback"

# Mörk redaktionell bas + en accentfärg per kategori (tidningens röda som bas).
CATEGORY_STYLES = {
    "Företag":   {"label": "Företag",   "accent": "#C41230", "tint": "#2B1A1E"},
    "Modeller":  {"label": "Modeller",  "accent": "#3E7CB1", "tint": "#1A222B"},
    "Politik":   {"label": "Politik",   "accent": "#B08A3E", "tint": "#2B261A"},
    "Verktyg":   {"label": "Verktyg",   "accent": "#4E8A5A", "tint": "#1A2B1F"},
    "Forskning": {"label": "Forskning", "accent": "#7A5EA8", "tint": "#221A2B"},
    "Säkerhet":  {"label": "Säkerhet",  "accent": "#C46112", "tint": "#2B221A"},
    "Energi":    {"label": "Energi",    "accent": "#C48A12", "tint": "#2B251A"},
    "default":   {"label": "AI-Bladet", "accent": "#C41230", "tint": "#222222"},
}


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "default"


def _svg(label: str, accent: str, tint: str) -> str:
    """1216x684 mörk gradient med diskret rutnät, kategoriord och wordmark."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1216" height="684" viewBox="0 0 1216 684" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1C1C1C"/>
      <stop offset="0.55" stop-color="{tint}"/>
      <stop offset="1" stop-color="#141414"/>
    </linearGradient>
    <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
      <path d="M48 0H0V48" fill="none" stroke="#FFFFFF" stroke-opacity="0.045" stroke-width="1"/>
    </pattern>
    <radialGradient id="glow" cx="0.78" cy="0.22" r="0.75">
      <stop offset="0" stop-color="{accent}" stop-opacity="0.30"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1216" height="684" fill="url(#bg)"/>
  <rect width="1216" height="684" fill="url(#grid)"/>
  <rect width="1216" height="684" fill="url(#glow)"/>
  <rect x="64" y="88" width="72" height="8" fill="{accent}"/>
  <text x="64" y="380" font-family="Georgia, 'Times New Roman', serif" font-size="112" font-weight="700" fill="#F5F1E8" letter-spacing="-2">{label}</text>
  <text x="64" y="440" font-family="Georgia, 'Times New Roman', serif" font-size="30" font-style="italic" fill="#F5F1E8" fill-opacity="0.55">Veckans AI-nyheter, på svenska</text>
  <text x="64" y="596" font-family="Helvetica, Arial, sans-serif" font-size="26" font-weight="700" fill="#F5F1E8">AI<tspan fill="{accent}">-Bladet</tspan></text>
  <rect x="0.5" y="0.5" width="1215" height="683" fill="none" stroke="#FFFFFF" stroke-opacity="0.08"/>
</svg>
'''


def ensure_all() -> None:
    """Skriv alla kategori-SVG:er (idempotent, skriver alltid om)."""
    STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)
    for name, style in CATEGORY_STYLES.items():
        path = STATIC_IMG_DIR / f"{_slug(name)}.svg"
        path.write_text(_svg(style["label"], style["accent"], style["tint"]),
                        encoding="utf-8")


def get(category: str) -> tuple[str, str]:
    """Returnera (absolut URL, credit) för en kategori-placeholder."""
    style = CATEGORY_STYLES.get(category) or CATEGORY_STYLES["default"]
    slug = _slug(category if category in CATEGORY_STYLES else "default")
    path = STATIC_IMG_DIR / f"{slug}.svg"
    if not path.exists():
        STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(_svg(style["label"], style["accent"], style["tint"]),
                        encoding="utf-8")
    return f"{SITE_URL}/img/fallback/{slug}.svg", "Grafik · AI-Bladet"


if __name__ == "__main__":
    ensure_all()
    print(f"✅ {len(CATEGORY_STYLES)} fallback-SVG:er skrivna till {STATIC_IMG_DIR}")
