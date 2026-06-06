"""
Système d'interface partagé pour le site Streamlit.

Un seul endroit pour le style : deux thèmes (sombre / clair), typographie,
métriques, boutons, en-têtes de page et callouts. Chaque page appelle
`start_page()` en tête, qui configure la page, affiche la bascule de thème
et injecte le CSS du thème courant ; elle renvoie la palette active (utile
pour colorer les graphes Plotly).
"""

from __future__ import annotations

import os

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
    return palette


def start_page(title: str, icon: str = "📈", layout: str = "wide") -> dict:
    """Configure la page, affiche la bascule de thème, injecte le style.

    Renvoie la palette active (à passer aux graphes Plotly).
    """
    _load_secrets_to_env()
    init_page(title, icon, layout)
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
