"""
Système d'interface partagé pour le site Streamlit.

Un seul endroit pour le style : couleurs (alignées sur DESIGN.md), typographie,
métriques, boutons, en-têtes de page et callouts. Chaque page appelle `setup_page()`
en tête pour hériter du même look.
"""

from __future__ import annotations

import streamlit as st

# Couleurs de marque (doublon volontaire de .streamlit/config.toml et DESIGN.md,
# pour pouvoir les utiliser dans le CSS injecté).
COLORS = {
    "bg": "#0f0f13",
    "surface": "#18191f",
    "border": "#31323a",
    "ink": "#f1f1f4",
    "muted": "#a9aab2",
    "primary": "#787cf0",
    "gain": "#51c672",
    "loss": "#f14d4c",
    "warn": "#edb345",
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg: #0f0f13; --surface: #18191f; --border: #31323a;
  --ink: #f1f1f4; --muted: #a9aab2; --primary: #787cf0;
  --gain: #51c672; --loss: #f14d4c; --warn: #edb345;
  --radius: 0.6rem;
  --ease: cubic-bezier(0.22, 1, 0.36, 1);
}

/* Typographie : une seule famille bien réglée (sans toucher aux icônes). */
.stApp, .stApp button, .stApp input, .stApp textarea, .stApp select,
.stApp p, .stApp span, .stApp label, .stApp li, .stApp div {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
/* Restaurer la police des icônes Material de Streamlit (ligatures). */
[data-testid="stIconMaterial"], .material-icons, .material-icons-outlined,
span[class*="material-symbols"], [class*="material-symbols"] {
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
               'Material Icons' !important;
}

.stApp { background: var(--bg); }

/* Largeur de lecture maîtrisée, padding haut réduit. */
.block-container { padding-top: 2.4rem; padding-bottom: 4rem; max-width: 1180px; }

/* Hiérarchie : échelle rem fixe, contraste de poids. */
h1 { font-size: 2.1rem; font-weight: 700; letter-spacing: -0.02em; }
h2 { font-size: 1.4rem; font-weight: 650; letter-spacing: -0.01em; margin-top: 0.4rem; }
h3 { font-size: 1.125rem; font-weight: 600; }
p, li, label, .stMarkdown { color: var(--ink); }

a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Sidebar : surface distincte du contenu. */
[data-testid="stSidebar"] {
  background: var(--surface);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

/* En-tête de page maison. */
.ta-header { margin: 0 0 1.6rem; }
.ta-header__title {
  font-size: 2.1rem; font-weight: 700; letter-spacing: -0.02em;
  color: var(--ink); line-height: 1.1; text-wrap: balance;
}
.ta-header__sub {
  color: var(--muted); font-size: 1rem; margin-top: 0.4rem; max-width: 68ch;
}
.ta-header__rule {
  height: 3px; width: 56px; margin-top: 0.9rem; border-radius: 99px;
  background: var(--primary);
}

/* Métriques : cartes sobres, chiffres tabulaires. */
[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.85rem 1rem;
  transition: border-color 180ms var(--ease);
}
[data-testid="stMetric"]:hover { border-color: #43444e; }
[data-testid="stMetricLabel"] {
  color: var(--muted); font-size: 0.78rem; font-weight: 500;
  letter-spacing: 0.01em;
}
[data-testid="stMetricValue"] {
  color: var(--ink); font-weight: 650; font-size: 1.55rem;
  font-variant-numeric: tabular-nums;
}
[data-testid="stMetricDelta"] { font-variant-numeric: tabular-nums; font-size: 0.82rem; }

/* Boutons : primaire indigo (texte sombre), états complets. */
.stButton > button, [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] {
  border-radius: var(--radius);
  font-weight: 600;
  transition: transform 160ms var(--ease), box-shadow 160ms var(--ease),
              background 160ms var(--ease), border-color 160ms var(--ease);
}
[data-testid="stBaseButton-primary"] {
  background: var(--primary); color: var(--bg); border: 1px solid var(--primary);
}
[data-testid="stBaseButton-primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px -6px rgba(120, 124, 240, 0.6);
  filter: brightness(1.06);
}
[data-testid="stBaseButton-secondary"] {
  background: var(--surface); color: var(--ink); border: 1px solid var(--border);
}
[data-testid="stBaseButton-secondary"]:hover { border-color: var(--primary); }
.stButton > button:active { transform: translateY(0); }
.stButton > button:focus-visible {
  outline: 2px solid var(--primary); outline-offset: 2px;
}

/* Champs de saisie : focus indigo cohérent. */
[data-baseweb="input"] input:focus, [data-baseweb="select"] [role="button"]:focus-within {
  outline: none;
}

/* Callouts maison (pas de bande latérale épaisse). */
.ta-callout {
  display: flex; gap: 0.7rem; align-items: flex-start;
  border-radius: var(--radius); padding: 0.85rem 1rem; margin: 0.5rem 0 1rem;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--ink); font-size: 0.92rem; line-height: 1.5;
}
.ta-callout__icon { font-size: 1.05rem; line-height: 1.4; }
.ta-callout--info   { border-color: #3a3c66; background: rgba(120,124,240,0.10); }
.ta-callout--warn   { border-color: #5a4a1f; background: rgba(237,179,69,0.10); }
.ta-callout--danger { border-color: #5a2b2b; background: rgba(241,77,76,0.10); }
.ta-callout--gain   { border-color: #2c5238; background: rgba(81,198,114,0.10); }

/* Tableaux & dataframes : chiffres alignés. */
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: var(--radius); }
[data-testid="stTable"] td, [data-testid="stDataFrame"] td { font-variant-numeric: tabular-nums; }

/* Alertes natives Streamlit : rayon et contour cohérents. */
[data-testid="stAlert"] { border-radius: var(--radius); }

/* Mouvement réduit : on neutralise les transitions. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; }
  [data-testid="stBaseButton-primary"]:hover { transform: none; }
}
</style>
"""


def setup_page(title: str, icon: str = "📈", layout: str = "wide") -> None:
    """Configure la page, injecte le style et l'en-tête. À appeler en tout premier."""
    st.set_page_config(page_title=f"{title} · Trading Assistant",
                       page_icon=icon, layout=layout)
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """En-tête de page cohérent : titre + sous-titre + filet d'accent."""
    prefix = f"{icon} " if icon else ""
    sub = f'<div class="ta-header__sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="ta-header">'
        f'<div class="ta-header__title">{prefix}{title}</div>'
        f'{sub}'
        f'<div class="ta-header__rule"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def callout(text: str, tone: str = "info", icon: str | None = None) -> None:
    """
    Encadré informatif. tone ∈ {info, warn, danger, gain}.

    Remplace st.info/warning par un style aligné sur la marque.
    """
    icones = {"info": "💡", "warn": "⚠️", "danger": "🛑", "gain": "✅"}
    ic = icon if icon is not None else icones.get(tone, "💡")
    st.markdown(
        f'<div class="ta-callout ta-callout--{tone}">'
        f'<span class="ta-callout__icon">{ic}</span><span>{text}</span></div>',
        unsafe_allow_html=True,
    )
