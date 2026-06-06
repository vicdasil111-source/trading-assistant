# Design

## Theme

Sombre, calme, « salle de marché avant l'ouverture ». Fond presque noir teinté
d'un soupçon d'indigo, un seul accent indigo qui porte l'identité, et des couleurs
sémantiques (vert/rouge/ambre) réservées au sens financier. Registre **product** :
familiarité gagnée, sobriété, l'outil s'efface devant la tâche.

Stratégie de couleur : **Restrained** (neutres teintés + un accent), avec le
vert/rouge comme vocabulaire d'état, pas comme décoration.

## Color palette (OKLCH → hex)

| Rôle | Token | OKLCH | Hex | Usage |
|---|---|---|---|---|
| Fond app | `--bg` | 0.17 0.008 279 | `#0f0f13` | Arrière-plan principal |
| Surface | `--surface` | 0.215 0.012 279 | `#18191f` | Panneaux, sidebar, cartes métriques |
| Bordure | `--border` | 0.32 0.014 279 | `#31323a` | Séparateurs, contours |
| Texte | `--ink` | 0.96 0.004 279 | `#f1f1f4` | Texte principal |
| Texte secondaire | `--muted` | 0.74 0.012 279 | `#a9aab2` | Légendes, labels |
| Primaire (marque) | `--primary` | 0.64 0.17 279 | `#787cf0` | Boutons, liens, sélection |
| Gain | `--gain` | 0.74 0.16 150 | `#51c672` | Rendements positifs, achat |
| Perte | `--loss` | 0.65 0.20 25 | `#f14d4c` | Rendements négatifs, vente |
| Alerte | `--warn` | 0.80 0.14 80 | `#edb345` | Surachat, avertissements |

Contraste : `--ink` et `--muted` sur `--bg` dépassent largement 4.5:1. Le texte
des boutons primaires est `--bg` (sombre) sur indigo, pour rester lisible.

## Typography

- **Famille unique : Inter** (sans-serif bien réglée, idéale produit). Mono :
  `ui-monospace` pour les blocs de code/chiffres bruts.
- Échelle **rem fixe** (pas de fluid), ratio ~1.2 : 0.8 / 0.875 / 1 / 1.125 /
  1.375 / 1.75 / 2.25 rem.
- **Chiffres tabulaires** (`font-variant-numeric: tabular-nums`) sur les métriques
  et tableaux : les colonnes de nombres s'alignent, lisibilité financière.
- Labels de métriques en petites capitales discrètes (≤ 1 mot ou 2), jamais de
  phrases en capitales.

## Components

- **Métriques** : carte sobre (surface + bordure + rayon 0.6rem), label `--muted`
  espacé, valeur en 1.6rem tabulaire, delta coloré par le sens.
- **Boutons** : primaire indigo (texte sombre), secondaire surface + bordure.
  États hover (léger lift + ombre), focus (anneau indigo visible), active.
- **Callouts** : fond teinté de la couleur de sens + bordure pleine fine + icône.
  Jamais de bande latérale épaisse (`border-left`).
- **En-tête de page** : titre + sous-titre + filet d'accent indigo. Cohérent sur
  toutes les pages.
- **Sidebar** : surface plus claire que le contenu, bordure droite.
- **Hero (accueil)** : grand titre `clamp()` (max ~3.2rem) avec un mot en accent
  indigo, sous-titre `--muted` ≤ 60ch, rangée de *chips* (pastille verte + label).
- **Marché en direct** : grille de tuiles `auto-fit minmax(160px)` ; chaque tuile =
  symbole, prix tabulaire, variation 24 h (flèche ▲/▼ + signe, doublée pour le
  daltonisme) et **sparkline SVG** (ligne + aire, couleur sémantique gain/perte).
- **Cartes de navigation** : liens `.ta-card` (icône + titre + description +
  « Ouvrir → »), hover lift + ombre indigo ; rythme varié (3 cartes phares puis
  pastilles compactes) pour éviter la grille de cartes identiques.

## Motion

150–220 ms, `ease` sortant. La couleur/élévation des états change en douceur ;
pas de chorégraphie au chargement. Les tuiles du marché ont une légère entrée
(`ta-rise`). `prefers-reduced-motion` respecté (transitions/animations neutralisées).

Ambiance : un voile radial indigo très discret (≈ 15 % d'opacité) en haut de
`.stApp`, fixe, derrière tout le contenu — assez subtil pour préserver les
contrastes WCAG AA. L'en-tête Streamlit est rendu transparent pour le laisser
transparaître.

## Layout

- `block-container` recentré, largeur de lecture maîtrisée, padding haut réduit.
- Métriques en lignes de colonnes ; tableaux denses autorisés.
- Responsive structurel (Streamlit empile les colonnes en petit écran).

## Implementation

- Tokens thème : `.streamlit/config.toml` (`[theme]`) + variables `:root` injectées
  par `utils/ui.py` selon le thème courant.
- Système d'UI partagé : `utils/ui.py` — `start_page()` (config + bascule de thème +
  CSS), `page_header()`, `callout()`, et les composants d'accueil `hero()`,
  `section()`, `market_pulse()`, `sparkline_svg()`, `feature_cards()`, `pill_links()`.
  Importé en tête de chaque page.
