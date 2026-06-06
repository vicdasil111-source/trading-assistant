"""
Système d'interface partagé pour le site Streamlit.

Un seul endroit pour le style : deux thèmes (sombre / clair), typographie,
métriques, boutons, en-têtes de page et callouts. Chaque page appelle
`start_page()` en tête, qui configure la page, affiche la bascule de thème
et injecte le CSS du thème courant ; elle renvoie la palette active (utile
pour colorer les graphes Plotly).
"""

from __future__ import annotations

import html as _html
import os
from urllib.parse import quote as _urlquote

import streamlit as st


def _load_secrets_to_env() -> None:
    """Recopie les secrets Streamlit (Supabase…) dans les variables d'environnement,
    pour que core/ les lise sans dépendre de Streamlit."""
    try:
        for k in ("SUPABASE_URL", "SUPABASE_KEY"):
            if k not in os.environ and k in st.secrets:
                os.environ[k] = str(st.secrets[k])
    except Exception:
        pass  # pas de fichier secrets en local : on reste sur SQLite

# Palettes (alignées sur DESIGN.md). Hex calculés depuis de l'OKLCH.
DARK = {
    "bg": "#0f0f13", "surface": "#18191f", "border": "#31323a",
    "ink": "#f1f1f4", "muted": "#a9aab2", "primary": "#787cf0", "on_primary": "#ffffff",
    "gain": "#51c672", "loss": "#f14d4c", "warn": "#edb345",
    "plotly": "plotly_dark", "grid": "#31323a", "bb_fill": "rgba(169,170,178,0.07)",
}
LIGHT = {
    "bg": "#ffffff", "surface": "#f6f6f9", "border": "#dddde3",
    "ink": "#242630", "muted": "#60626f", "primary": "#5755cd", "on_primary": "#ffffff",
    "gain": "#0e8c41", "loss": "#c9222b", "warn": "#9f7100",
    "plotly": "plotly_white", "grid": "#dddde3", "bb_fill": "rgba(96,98,111,0.08)",
}
# Thème « Terminal » néon, inspiré des terminaux on-chain (Axiom / Photon).
TERMINAL = {
    "bg": "#07090c", "surface": "#0f141a", "border": "#1f2a33",
    "ink": "#e8f1f2", "muted": "#8a97a1", "primary": "#22d3ee", "on_primary": "#04181c",
    "gain": "#34e29b", "loss": "#ff5470", "warn": "#ffd24d",
    "plotly": "plotly_dark", "grid": "#1f2a33", "bb_fill": "rgba(138,151,161,0.07)",
}

THEMES = {"dark": DARK, "light": LIGHT, "terminal": TERMINAL}

# Conservé pour compatibilité (anciens imports) : palette sombre par défaut.
COLORS = DARK


def current_theme() -> str:
    return st.session_state.get("theme", "dark")


def current_colors() -> dict:
    return THEMES.get(current_theme(), DARK)


def _css(p: dict) -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {{
  --bg: {p['bg']}; --surface: {p['surface']}; --border: {p['border']};
  --ink: {p['ink']}; --muted: {p['muted']}; --primary: {p['primary']};
  --on-primary: {p['on_primary']};
  --gain: {p['gain']}; --loss: {p['loss']}; --warn: {p['warn']};
  --radius: 0.6rem;
  --ease: cubic-bezier(0.22, 1, 0.36, 1);
}}

/* Typographie : une seule famille bien réglée (sans toucher aux icônes). */
.stApp, .stApp button, .stApp input, .stApp textarea, .stApp select,
.stApp p, .stApp span, .stApp label, .stApp li, .stApp div {{
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
[data-testid="stIconMaterial"], .material-icons, .material-icons-outlined,
span[class*="material-symbols"], [class*="material-symbols"] {{
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
               'Material Icons' !important;
}}

.stApp, [data-testid="stHeader"] {{ background: var(--bg); }}
.stApp, .stApp p, .stApp li, .stApp label, .stMarkdown {{ color: var(--ink); }}

.block-container {{ padding-top: 2.4rem; padding-bottom: 4rem; max-width: 1180px; }}

h1 {{ font-size: 2.1rem; font-weight: 700; letter-spacing: -0.02em; color: var(--ink); }}
h2 {{ font-size: 1.4rem; font-weight: 650; letter-spacing: -0.01em; color: var(--ink); }}
h3 {{ font-size: 1.125rem; font-weight: 600; color: var(--ink); }}

a {{ color: var(--primary); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: var(--surface); border-right: 1px solid var(--border); }}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}
[data-testid="stSidebar"] * {{ color: var(--ink); }}

/* Champs natifs (input, select, textarea) : suivent le thème. */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input,
.stTextArea textarea, [data-baseweb="select"] [role="combobox"] {{
  background-color: var(--bg) !important;
  color: var(--ink) !important;
  border-color: var(--border) !important;
}}
[data-testid="stWidgetLabel"] label, .stSlider label {{ color: var(--ink) !important; }}
[data-baseweb="slider"] [role="slider"] {{ background: var(--primary) !important; }}
/* Boutons +/- des champs numériques : suivent le thème. */
[data-testid="stNumberInput"] button {{ background: var(--surface) !important;
  color: var(--ink) !important; border-color: var(--border) !important; }}
[data-testid="stNumberInput"] button:hover {{ border-color: var(--primary) !important; }}
/* Menu déroulant des selectbox (popover). */
[data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] {{
  background: var(--surface) !important; color: var(--ink) !important; }}

/* Expander, code, tableaux */
[data-testid="stExpander"] details {{ border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }}
[data-testid="stExpander"] summary {{ color: var(--ink); }}
pre, code, [data-testid="stCode"] {{ background: var(--surface) !important; color: var(--ink) !important; }}
[data-testid="stTable"] {{ color: var(--ink); }}
[data-testid="stTable"] th {{ color: var(--muted); font-weight: 600; }}
[data-testid="stTable"] td, [data-testid="stTable"] th {{ border-color: var(--border) !important; font-variant-numeric: tabular-nums; }}

/* En-tête de page maison. */
.ta-header {{ margin: 0 0 1.6rem; }}
.ta-header__title {{ font-size: 2.1rem; font-weight: 700; letter-spacing: -0.02em;
  color: var(--ink); line-height: 1.1; text-wrap: balance; }}
.ta-header__sub {{ color: var(--muted); font-size: 1rem; margin-top: 0.4rem; max-width: 68ch; }}
.ta-header__rule {{ height: 3px; width: 56px; margin-top: 0.9rem; border-radius: 99px; background: var(--primary); }}

/* Métriques en cartes, chiffres tabulaires. */
[data-testid="stMetric"] {{ background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 0.85rem 1rem; transition: border-color 180ms var(--ease); }}
[data-testid="stMetric"]:hover {{ border-color: var(--primary); }}
[data-testid="stMetricLabel"] {{ color: var(--muted); font-size: 0.78rem; font-weight: 500; }}
[data-testid="stMetricLabel"] * {{ color: var(--muted) !important; }}
[data-testid="stMetricValue"] {{ color: var(--ink); font-weight: 650; font-size: 1.55rem; font-variant-numeric: tabular-nums; }}
[data-testid="stMetricDelta"] {{ font-variant-numeric: tabular-nums; font-size: 0.82rem; }}

@keyframes ta-rise {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
[data-testid="stMetric"] {{ animation: ta-rise 380ms var(--ease) both; }}
[data-testid="stColumn"]:nth-of-type(2) [data-testid="stMetric"] {{ animation-delay: 55ms; }}
[data-testid="stColumn"]:nth-of-type(3) [data-testid="stMetric"] {{ animation-delay: 110ms; }}
[data-testid="stColumn"]:nth-of-type(4) [data-testid="stMetric"] {{ animation-delay: 165ms; }}
[data-testid="stColumn"]:nth-of-type(5) [data-testid="stMetric"] {{ animation-delay: 220ms; }}

/* Boutons : primaire indigo, états complets. */
.stButton > button {{ border-radius: var(--radius); font-weight: 600;
  transition: transform 160ms var(--ease), box-shadow 160ms var(--ease), border-color 160ms var(--ease); }}
[data-testid="stBaseButton-primary"] {{ background: var(--primary); color: var(--on-primary); border: 1px solid var(--primary); }}
[data-testid="stBaseButton-primary"]:hover {{ transform: translateY(-1px); box-shadow: 0 6px 22px -6px var(--primary); filter: brightness(1.08); }}
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] {{ background: var(--surface); color: var(--ink); border: 1px solid var(--border); }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color: var(--primary); }}
.stDownloadButton > button {{ background: var(--surface); color: var(--ink); border: 1px solid var(--border); border-radius: var(--radius); font-weight: 600; }}
.stDownloadButton > button:hover {{ border-color: var(--primary); }}
.stButton > button:active {{ transform: translateY(0); }}
.stButton > button:focus-visible {{ outline: 2px solid var(--primary); outline-offset: 2px; }}

/* Callouts (pas de bande latérale épaisse). */
.ta-callout {{ display: flex; gap: 0.7rem; align-items: flex-start; border-radius: var(--radius);
  padding: 0.85rem 1rem; margin: 0.5rem 0 1rem; border: 1px solid var(--border);
  background: var(--surface); color: var(--ink); font-size: 0.92rem; line-height: 1.5; }}
.ta-callout__icon {{ font-size: 1.05rem; line-height: 1.4; }}
.ta-callout--info   {{ border-color: color-mix(in oklab, var(--primary) 45%, var(--border)); background: color-mix(in oklab, var(--primary) 12%, var(--bg)); }}
.ta-callout--warn   {{ border-color: color-mix(in oklab, var(--warn) 45%, var(--border)); background: color-mix(in oklab, var(--warn) 12%, var(--bg)); }}
.ta-callout--danger {{ border-color: color-mix(in oklab, var(--loss) 45%, var(--border)); background: color-mix(in oklab, var(--loss) 12%, var(--bg)); }}
.ta-callout--gain   {{ border-color: color-mix(in oklab, var(--gain) 45%, var(--border)); background: color-mix(in oklab, var(--gain) 12%, var(--bg)); }}

[data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: var(--radius); }}
[data-testid="stAlert"] {{ border-radius: var(--radius); }}

/* Petit badge "thème" plus discret dans la sidebar. */
[data-testid="stSidebar"] [role="radiogroup"] {{ gap: 0.3rem; }}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition: none !important; animation: none !important; }}
  [data-testid="stBaseButton-primary"]:hover {{ transform: none; }}
}}
</style>
"""


# CSS « composants » statique (tokens var(--…) déjà posés par _css). Pas une
# f-string : pas de doublage d'accolades, plus sûr à maintenir.
_STATIC_CSS = """
<style>
/* ---------- Ambiance : un voile indigo très discret derrière toute l'app. ---------- */
.stApp {
  background:
    radial-gradient(62% 44% at 50% -12%,
      color-mix(in oklab, var(--primary) 15%, transparent), transparent 72%),
    radial-gradient(46% 30% at 100% 2%,
      color-mix(in oklab, var(--gain) 6%, transparent), transparent 60%),
    var(--bg);
  background-attachment: fixed;
}
[data-testid="stHeader"] { background: transparent; }

/* ---------- Hero ---------- */
.ta-hero { position: relative; padding: 1.2rem 0 1.4rem; }
.ta-hero__title {
  font-size: clamp(2.1rem, 1.4rem + 2.6vw, 3.2rem); font-weight: 760;
  letter-spacing: -0.035em; line-height: 1.04; color: var(--ink);
  text-wrap: balance; margin: 0;
}
.ta-hero__accent { color: var(--primary); }
.ta-hero__sub {
  color: var(--muted); font-size: 1.06rem; line-height: 1.55;
  margin: 0.8rem 0 0; max-width: 60ch; text-wrap: pretty;
}
.ta-chips { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.15rem; }
.ta-chip {
  display: inline-flex; align-items: center; gap: 0.45rem;
  font-size: 0.8rem; font-weight: 550; color: var(--muted);
  background: var(--surface); border: 1px solid var(--border);
  padding: 0.34rem 0.72rem; border-radius: 999px;
}
.ta-chip::before {
  content: ""; width: 6px; height: 6px; border-radius: 999px; background: var(--gain);
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--gain) 25%, transparent);
}

/* ---------- Titre de section ---------- */
.ta-sec { display: flex; align-items: baseline; justify-content: space-between;
  gap: 1rem; margin: 2.3rem 0 0.95rem; }
.ta-sec__title { font-size: 1.2rem; font-weight: 650; color: var(--ink); letter-spacing: -0.01em; }
.ta-sec__note { font-size: 0.85rem; color: var(--muted); white-space: nowrap; }

/* ---------- Marché en direct ---------- */
.ta-pulse { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.7rem; }
.ta-tile {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 0.85rem 0.95rem 0.7rem; overflow: hidden;
  transition: border-color 180ms var(--ease), transform 180ms var(--ease);
  animation: ta-rise 460ms var(--ease) both;
}
.ta-tile:hover { border-color: color-mix(in oklab, var(--primary) 55%, var(--border)); transform: translateY(-2px); }
.ta-tile__head { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.ta-tile__sym { font-weight: 650; font-size: 0.98rem; color: var(--ink); letter-spacing: -0.01em; }
.ta-tile__chg { font-size: 0.8rem; font-weight: 650; font-variant-numeric: tabular-nums; white-space: nowrap; }
.ta-up { color: var(--gain); }
.ta-down { color: var(--loss); }
.ta-flat { color: var(--muted); }
.ta-tile__price { font-size: 1.34rem; font-weight: 650; color: var(--ink);
  font-variant-numeric: tabular-nums; margin: 0.18rem 0 0.05rem; }
.ta-tile__unit { font-size: 0.72rem; color: var(--muted); font-weight: 500; margin-left: 0.28rem; }
.ta-spark { display: block; width: 100%; height: 38px; margin-top: 0.35rem; }

/* ---------- Cartes de navigation (liens) ---------- */
.ta-feat { display: grid; grid-template-columns: repeat(auto-fit, minmax(232px, 1fr)); gap: 0.8rem; }
.ta-card {
  display: flex; flex-direction: column; gap: 0.3rem; text-decoration: none !important;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1.05rem 1.1rem;
  transition: border-color 180ms var(--ease), transform 180ms var(--ease), box-shadow 180ms var(--ease);
}
.ta-card:hover { border-color: color-mix(in oklab, var(--primary) 60%, var(--border));
  transform: translateY(-3px); box-shadow: 0 16px 42px -24px var(--primary); }
.ta-card__ic { font-size: 1.55rem; line-height: 1; margin-bottom: 0.15rem; }
.ta-card__t { font-size: 1.02rem; font-weight: 650; color: var(--ink) !important; }
.ta-card__d { font-size: 0.875rem; color: var(--muted); line-height: 1.45; }
.ta-card__go { margin-top: 0.4rem; font-size: 0.82rem; font-weight: 650; color: var(--primary); }

.ta-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.3rem; }
.ta-pill {
  display: inline-flex; align-items: center; gap: 0.45rem; text-decoration: none !important;
  background: var(--surface); border: 1px solid var(--border); border-radius: 999px;
  padding: 0.44rem 0.85rem; font-size: 0.875rem; font-weight: 550; color: var(--ink) !important;
  transition: border-color 160ms var(--ease), transform 160ms var(--ease); }
.ta-pill:hover { border-color: var(--primary); transform: translateY(-1px); }
.ta-pill__ic { font-size: 0.98rem; }

/* ---------- Tuiles cliquables + badges (page Marché) ---------- */
a.ta-tile { text-decoration: none !important; color: inherit; display: block; cursor: pointer; }
.ta-tile__pair { color: var(--muted); font-weight: 500; font-size: 0.82rem; }
.ta-tile__foot { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.55rem; }
.ta-badge { font-size: 0.72rem; font-weight: 600; color: var(--muted);
  background: color-mix(in oklab, var(--muted) 12%, transparent);
  border: 1px solid var(--border); border-radius: 999px; padding: 0.16rem 0.5rem;
  font-variant-numeric: tabular-nums; }
.ta-badge--buy { color: var(--gain); border-color: color-mix(in oklab, var(--gain) 40%, var(--border));
  background: color-mix(in oklab, var(--gain) 14%, transparent); }
.ta-badge--sell { color: var(--loss); border-color: color-mix(in oklab, var(--loss) 40%, var(--border));
  background: color-mix(in oklab, var(--loss) 14%, transparent); }

/* ---------- Indicateur « en direct » (traduit un état : données live) ---------- */
.ta-live { display: inline-flex; align-items: center; gap: 0.4rem; color: var(--muted); }
.ta-live__dot { width: 8px; height: 8px; border-radius: 999px; background: var(--gain);
  animation: ta-ping 2.1s var(--ease) infinite; }
@keyframes ta-ping {
  0%   { box-shadow: 0 0 0 0 color-mix(in oklab, var(--gain) 55%, transparent); }
  70%  { box-shadow: 0 0 0 7px color-mix(in oklab, var(--gain) 0%, transparent); }
  100% { box-shadow: 0 0 0 0 color-mix(in oklab, var(--gain) 0%, transparent); }
}

/* ---------- Squelettes de chargement (mieux qu'un spinner) ---------- */
.ta-skel { position: relative; overflow: hidden; }
.ta-skel::after { content: ""; position: absolute; inset: 0; transform: translateX(-100%);
  background: linear-gradient(90deg, transparent,
    color-mix(in oklab, var(--ink) 9%, transparent), transparent);
  animation: ta-shimmer 1.25s var(--ease) infinite; }
@keyframes ta-shimmer { to { transform: translateX(100%); } }
.ta-skel-line { background: color-mix(in oklab, var(--muted) 22%, transparent); border-radius: 6px; height: 0.85rem; }
.ta-skel-line.tall { height: 1.35rem; margin: 0.35rem 0; }
.ta-skel-line.w40 { width: 40%; } .ta-skel-line.w70 { width: 70%; }
.ta-skel-spark { margin-top: 0.5rem; height: 38px; border-radius: 8px;
  background: color-mix(in oklab, var(--muted) 13%, transparent); }
.ta-skel-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.7rem; margin-bottom: 0.6rem; }
.ta-skel-metric { height: 90px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }

/* ---------- Recherche d'actif (accueil) ---------- */
.ta-find { font-size: 0.92rem; font-weight: 600; color: var(--muted); margin: 1.4rem 0 0.4rem; }

/* ---------- Navigation groupée (sidebar) ---------- */
.ta-nav-brand { font-weight: 700; font-size: 1.05rem; letter-spacing: -0.015em;
  color: var(--ink); margin: 0.1rem 0 0.5rem; }
.ta-nav-group { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.07em;
  text-transform: uppercase; color: var(--muted); margin: 0.95rem 0 0.2rem; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a { border-radius: 8px;
  padding: 0.28rem 0.5rem; transition: background 140ms var(--ease); }
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
  background: color-mix(in oklab, var(--primary) 13%, transparent); }
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
[data-testid="stSidebar"] [data-testid="stPageLink"] a[data-active="true"] {
  background: color-mix(in oklab, var(--primary) 18%, transparent); }
.ta-nav-sep { height: 1px; background: var(--border); margin: 0.9rem 0 0.2rem; }

/* ---------- Actualités (journaux en direct) ---------- */
.ta-news { display: grid; gap: 0.6rem; }
.ta-news-item { display: block; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius); padding: 0.85rem 1rem;
  transition: border-color 160ms var(--ease), transform 160ms var(--ease); }
.ta-news-item:hover { border-color: color-mix(in oklab, var(--primary) 55%, var(--border));
  transform: translateY(-2px); }
a.ta-news-title { display: block; text-decoration: none !important; color: var(--ink) !important;
  font-weight: 600; font-size: 0.98rem; line-height: 1.35; }
a.ta-news-title:hover { color: var(--primary) !important; }
.ta-news-foot { display: flex; align-items: center; justify-content: space-between;
  gap: 0.6rem; flex-wrap: wrap; margin-top: 0.45rem; }
.ta-news-meta { color: var(--muted); font-size: 0.8rem; }
.ta-news-tags { display: flex; gap: 0.3rem; flex-wrap: wrap; }
.ta-news-tag { text-decoration: none !important; font-size: 0.72rem; font-weight: 650;
  color: var(--primary) !important; background: color-mix(in oklab, var(--primary) 12%, transparent);
  border: 1px solid color-mix(in oklab, var(--primary) 30%, var(--border));
  border-radius: 999px; padding: 0.1rem 0.45rem; }
.ta-news-tag:hover { background: color-mix(in oklab, var(--primary) 22%, transparent); }

/* ---------- Sentiment (Fear & Greed) ---------- */
.ta-fng { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1rem 1.1rem; max-width: 520px; }
.ta-fng__top { display: flex; align-items: baseline; justify-content: space-between; gap: 0.6rem; }
.ta-fng__val { font-size: 1.9rem; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }
.ta-fng__max { font-size: 0.9rem; font-weight: 500; color: var(--muted); }
.ta-fng__label { font-size: 0.95rem; font-weight: 650; color: var(--ink); }
.ta-fng__bar { position: relative; height: 8px; border-radius: 999px; margin: 0.7rem 0 0.35rem;
  background: linear-gradient(90deg, var(--loss), var(--warn), var(--gain)); }
.ta-fng__marker { position: absolute; top: 50%; width: 14px; height: 14px; border-radius: 999px;
  background: var(--ink); border: 2px solid var(--bg); transform: translate(-50%, -50%);
  box-shadow: 0 1px 4px rgba(0,0,0,0.4); }
.ta-fng__scale { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--muted); }
.ta-fng__note { font-size: 0.76rem; color: var(--muted); margin-top: 0.5rem; }

@media (prefers-reduced-motion: reduce) {
  .stApp { background-attachment: scroll; }
  .ta-tile, .ta-card, .ta-pill, .ta-live__dot,
  .ta-skel::after, .ta-news-item { animation: none !important; transition: none !important; }
  .ta-tile:hover, .ta-card:hover, .ta-pill:hover, .ta-news-item:hover { transform: none !important; }
}
</style>
"""


# Navigation PAR SECTIONS (la nav auto de Streamlit est masquée via config.toml).
# Chaque entrée : (chemin du fichier, libellé, icône).
NAV_GROUPS = [
    ("Découvrir", [
        ("dashboard.py", "Accueil", "🏠"),
        ("pages/10_Marche.py", "Marché", "🛰️"),
        ("pages/15_Actualites.py", "Actualités", "📰"),
    ]),
    ("Automatiser", [
        ("pages/1_Optimisation.py", "Optimisation", "⚙️"),
        ("pages/2_Pilote_auto.py", "Pilote auto", "🤖"),
        ("pages/3_Machine_learning.py", "Machine Learning", "🧠"),
    ]),
    ("Outils", [
        ("pages/7_Comparateur.py", "Comparateur", "📊"),
        ("pages/6_Outils.py", "Outils & risque", "🧰"),
    ]),
    ("Mon espace", [
        ("pages/4_Compte.py", "Compte", "👤"),
        ("pages/5_Watchlist.py", "Watchlist", "⭐"),
        ("pages/8_Portefeuille.py", "Portefeuille", "💼"),
        ("pages/9_Alertes.py", "Alertes", "🔔"),
    ]),
    ("Trading", [
        ("pages/11_Trading_testnet.py", "Trading testnet", "🧪"),
        ("pages/12_Trading_reel.py", "Trading réel", "⚡"),
    ]),
    ("Aide", [
        ("pages/14_Assistant.py", "Assistant", "💬"),
        ("pages/13_Aide_et_FAQ.py", "Aide & FAQ", "❓"),
    ]),
]


def sidebar_nav() -> None:
    """Affiche la navigation regroupée par sections en haut de la sidebar."""
    with st.sidebar:
        st.markdown('<div class="ta-nav-brand">📈 Trading Assistant</div>',
                    unsafe_allow_html=True)
        for titre, items in NAV_GROUPS:
            st.markdown(f'<div class="ta-nav-group">{titre}</div>', unsafe_allow_html=True)
            for path, label, icon in items:
                try:
                    st.page_link(path, label=label, icon=icon)
                except Exception:
                    pass  # page absente : on l'ignore plutôt que de casser la nav
        st.markdown('<div class="ta-nav-sep"></div>', unsafe_allow_html=True)


def init_page(title: str, icon: str = "📈", layout: str = "wide") -> None:
    """Première commande Streamlit de la page (set_page_config)."""
    st.set_page_config(page_title=f"{title} · Trading Assistant",
                       page_icon=icon, layout=layout)


def _theme_toggle() -> None:
    """Bascule de thème dans la sidebar. Doit être appelée avant inject_theme()."""
    labels = {"dark": "🌙 Calme", "light": "☀️ Clair", "terminal": "🖥️ Terminal"}
    with st.sidebar:
        st.radio(
            "Apparence",
            options=["dark", "light", "terminal"],
            format_func=lambda v: labels[v],
            horizontal=True,
            key="theme",
        )


def inject_theme() -> dict:
    """Injecte le CSS du thème courant et renvoie la palette active."""
    palette = current_colors()
    st.markdown(_css(palette), unsafe_allow_html=True)
    st.markdown(_STATIC_CSS, unsafe_allow_html=True)
    return palette


def start_page(title: str, icon: str = "📈", layout: str = "wide") -> dict:
    """Configure la page, affiche la bascule de thème, injecte le style.

    Renvoie la palette active (à passer aux graphes Plotly).
    """
    _load_secrets_to_env()
    init_page(title, icon, layout)
    sidebar_nav()
    _theme_toggle()
    palette = inject_theme()
    # Import paresseux : account_ui importe utils.ui ; à ce stade ui est chargé.
    try:
        from utils import account_ui
        account_ui.sidebar_account()
    except Exception:  # ne jamais casser la page pour l'affichage du compte
        pass
    return palette


# Compat : ancien nom utilisé par certaines pages.
def setup_page(title: str, icon: str = "📈", layout: str = "wide") -> dict:
    return start_page(title, icon, layout)


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """En-tête de page cohérent : titre + sous-titre + filet d'accent."""
    prefix = f"{icon} " if icon else ""
    sub = f'<div class="ta-header__sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="ta-header"><div class="ta-header__title">{prefix}{title}</div>'
        f'{sub}<div class="ta-header__rule"></div></div>',
        unsafe_allow_html=True,
    )


def callout(text: str, tone: str = "info", icon: str | None = None) -> None:
    """Encadré informatif. tone ∈ {info, warn, danger, gain}."""
    icones = {"info": "💡", "warn": "⚠️", "danger": "🛑", "gain": "✅"}
    ic = icon if icon is not None else icones.get(tone, "💡")
    st.markdown(
        f'<div class="ta-callout ta-callout--{tone}">'
        f'<span class="ta-callout__icon">{ic}</span><span>{text}</span></div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Composants « accueil » : hero, titres de section, marché en direct, navigation.
# -----------------------------------------------------------------------------
def hero(title_html: str, subtitle: str = "", chips: list[str] | None = None) -> None:
    """Grand en-tête d'accueil. `title_html` peut contenir
    <span class="ta-hero__accent">…</span> pour colorer un mot."""
    sub = f'<p class="ta-hero__sub">{subtitle}</p>' if subtitle else ""
    chip_html = ""
    if chips:
        items = "".join(f'<span class="ta-chip">{c}</span>' for c in chips)
        chip_html = f'<div class="ta-chips">{items}</div>'
    st.markdown(
        f'<div class="ta-hero"><h1 class="ta-hero__title">{title_html}</h1>'
        f"{sub}{chip_html}</div>",
        unsafe_allow_html=True,
    )


def section(title: str, note: str = "", live: bool = False) -> None:
    """Titre de section avec note alignée à droite (optionnelle).

    `live=True` ajoute une pastille verte qui pulse (= données en direct, traduit
    un état réel — pas de la décoration)."""
    inner = note
    if live:
        inner = f'<span class="ta-live"><span class="ta-live__dot"></span>{note or "en direct"}</span>'
    note_html = f'<div class="ta-sec__note">{inner}</div>' if inner else ""
    st.markdown(
        f'<div class="ta-sec"><div class="ta-sec__title">{title}</div>{note_html}</div>',
        unsafe_allow_html=True,
    )


def _fmt_price(price: float) -> str:
    if price >= 100:
        s = f"{price:,.0f}"
    elif price >= 1:
        s = f"{price:,.2f}"
    else:
        s = f"{price:,.4f}"
    return s.replace(",", " ")  # espace fine insécable, élégance FR


def sparkline_svg(values, color: str, width: int = 140, height: int = 38) -> str:
    """Mini-courbe SVG (ligne + aire) à partir d'une liste de valeurs."""
    vals = [float(v) for v in values if v == v]  # retire les NaN
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    n = len(vals)
    pad = 3.0
    pts = []
    for i, v in enumerate(vals):
        x = i / (n - 1) * width
        y = height - pad - ((v - lo) / span) * (height - 2 * pad)
        pts.append((x, y))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,{height} {line} {width},{height}"
    lx, ly = pts[-1]
    return (
        f'<svg class="ta-spark" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" aria-hidden="true">'
        f'<polygon points="{area}" fill="{color}" opacity="0.12"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="1.8" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.4" fill="{color}"/></svg>'
    )


def _grid_html(items: list[dict], palette: dict, link: bool = True) -> str:
    """Construit le HTML d'une grille de tuiles marche (voir market_grid)."""
    if not items:
        return ('<div class="ta-callout ta-callout--warn">'
                '<span class="ta-callout__icon">⚠️</span><span>Marche momentanement '
                'indisponible, reessaie dans un instant.</span></div>')
    tiles = []
    for it in items:
        chg = it["chg"]
        if chg > 0.05:
            cls, arrow, color = "ta-up", "▲", palette["gain"]
        elif chg < -0.05:
            cls, arrow, color = "ta-down", "▼", palette["loss"]
        else:
            cls, arrow, color = "ta-flat", "▪", palette["muted"]
        base = it["symbol"].split("/")[0]

        foot = []
        rsi = it.get("rsi")
        if rsi is not None and rsi == rsi:  # exclut NaN
            foot.append(f'<span class="ta-badge">RSI {rsi:.0f}</span>')
        if it.get("trend"):
            foot.append(f'<span class="ta-badge">{it["trend"]}</span>')
        sig = it.get("signal")
        if sig == 1:
            foot.append('<span class="ta-badge ta-badge--buy">● Achat</span>')
        elif sig == -1:
            foot.append('<span class="ta-badge ta-badge--sell">● Vente</span>')
        foot_html = f'<div class="ta-tile__foot">{"".join(foot)}</div>' if foot else ""

        inner = (
            f'<div class="ta-tile__head"><span class="ta-tile__sym">{base}</span>'
            f'<span class="ta-tile__chg {cls}">{arrow} {abs(chg):.2f} %</span></div>'
            f'<div class="ta-tile__price">{_fmt_price(it["price"])}'
            f'<span class="ta-tile__unit">USDT</span></div>'
            f'{sparkline_svg(it["spark"], color)}{foot_html}'
        )
        if link:
            href = "/?symbol=" + _urlquote(it["symbol"], safe="")
            tiles.append(f'<a class="ta-tile" href="{href}" target="_self">{inner}</a>')
        else:
            tiles.append(f'<div class="ta-tile">{inner}</div>')
    return f'<div class="ta-pulse">{"".join(tiles)}</div>'


def market_grid(items: list[dict], palette: dict, link: bool = True) -> None:
    """Rend une grille de tuiles marche cliquables (voir _grid_html)."""
    st.markdown(_grid_html(items, palette, link), unsafe_allow_html=True)


def market_grid_html(items: list[dict], palette: dict, link: bool = True) -> str:
    """Comme market_grid mais renvoie le HTML (pour un st.empty placeholder)."""
    return _grid_html(items, palette, link)


def skeleton_market(tiles: int = 8, metrics: int = 0) -> str:
    """HTML de squelettes scintillants pendant le chargement du marche."""
    mrow = ""
    if metrics:
        cells = "".join('<div class="ta-skel-metric ta-skel"></div>' for _ in range(metrics))
        mrow = f'<div class="ta-skel-metrics">{cells}</div>'
    cell = ('<div class="ta-tile ta-skel"><div class="ta-skel-line w40"></div>'
            '<div class="ta-skel-line tall w70"></div><div class="ta-skel-spark"></div></div>')
    return f'{mrow}<div class="ta-pulse">{cell * tiles}</div>'


def market_pulse(items: list[dict], palette: dict) -> None:  # legacy, voir market_grid
    """Grille de tuiles « prix + variation + sparkline ».

    Chaque item : {symbol, price, chg, spark(list[float])}.
    """
    if not items:
        callout("Marché momentanément indisponible — réessaie dans un instant.", tone="warn")
        return
    tiles = []
    for it in items:
        chg = it["chg"]
        if chg > 0.05:
            cls, arrow, color = "ta-up", "▲", palette["gain"]
        elif chg < -0.05:
            cls, arrow, color = "ta-down", "▼", palette["loss"]
        else:
            cls, arrow, color = "ta-flat", "▪", palette["muted"]
        base = it["symbol"].split("/")[0]
        tiles.append(
            f'<div class="ta-tile"><div class="ta-tile__head">'
            f'<span class="ta-tile__sym">{base}</span>'
            f'<span class="ta-tile__chg {cls}">{arrow} {abs(chg):.2f} %</span></div>'
            f'<div class="ta-tile__price">{_fmt_price(it["price"])}'
            f'<span class="ta-tile__unit">USDT</span></div>'
            f'{sparkline_svg(it["spark"], color)}</div>'
        )
    st.markdown(f'<div class="ta-pulse">{"".join(tiles)}</div>', unsafe_allow_html=True)


def feature_cards(cards: list[dict]) -> None:
    """Cartes-liens « phares ». Chaque carte : {href, icon, title, desc}."""
    html = []
    for c in cards:
        html.append(
            f'<a class="ta-card" href="{c["href"]}" target="_self">'
            f'<span class="ta-card__ic">{c["icon"]}</span>'
            f'<span class="ta-card__t">{c["title"]}</span>'
            f'<span class="ta-card__d">{c["desc"]}</span>'
            f'<span class="ta-card__go">Ouvrir →</span></a>'
        )
    st.markdown(f'<div class="ta-feat">{"".join(html)}</div>', unsafe_allow_html=True)


def pill_links(items: list[dict]) -> None:
    """Liens compacts en pastilles. Chaque item : {href, icon, label}."""
    html = []
    for it in items:
        html.append(
            f'<a class="ta-pill" href="{it["href"]}" target="_self">'
            f'<span class="ta-pill__ic">{it["icon"]}</span>{it["label"]}</a>'
        )
    st.markdown(f'<div class="ta-pills">{"".join(html)}</div>', unsafe_allow_html=True)


def news_cards(items: list[dict]) -> None:
    """Liste d'actualités : titre cliquable (article) + source/date + pastilles
    des actifs mentionnés (lien vers l'analyse). HTML échappé (contenu externe)."""
    if not items:
        callout("Actualités indisponibles pour le moment — réessaie plus tard.", tone="warn")
        return
    cards = []
    for it in items:
        title = _html.escape(it.get("title", ""))
        link = _html.escape(it.get("link", "#"), quote=True)
        meta = " · ".join(x for x in (it.get("source", ""), it.get("date", "")) if x)
        meta = _html.escape(meta)
        tags = ""
        assets = it.get("assets") or []
        if assets:
            chips = "".join(
                f'<a class="ta-news-tag" href="/?symbol={_urlquote(sym, safe="")}" '
                f'target="_self">{_html.escape(sym.split("/")[0])}</a>'
                for sym in assets)
            tags = f'<span class="ta-news-tags">{chips}</span>'
        cards.append(
            f'<div class="ta-news-item">'
            f'<a class="ta-news-title" href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>'
            f'<div class="ta-news-foot"><span class="ta-news-meta">{meta}</span>{tags}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="ta-news">{"".join(cards)}</div>', unsafe_allow_html=True)


def sentiment_card(fng: dict | None) -> None:
    """Jauge « Fear & Greed » (sentiment du marché). Silencieux si indisponible."""
    if not fng:
        return
    val = max(0, min(100, int(fng.get("value", 0))))
    label = _html.escape(fng.get("label_fr") or fng.get("label", ""))
    st.markdown(
        f'<div class="ta-fng">'
        f'<div class="ta-fng__top">'
        f'<span class="ta-fng__val">{val}<span class="ta-fng__max">/100</span></span>'
        f'<span class="ta-fng__label">{label}</span></div>'
        f'<div class="ta-fng__bar"><span class="ta-fng__marker" style="left:{val}%"></span></div>'
        f'<div class="ta-fng__scale"><span>Peur</span><span>Neutre</span><span>Avidité</span></div>'
        f'<div class="ta-fng__note">Indice Fear &amp; Greed — humeur du marché, '
        f'pas un signal d\'achat.</div></div>',
        unsafe_allow_html=True,
    )
