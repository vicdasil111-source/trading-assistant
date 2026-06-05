# Trading Assistant — Document de Design

**Date :** 2026-06-05
**Auteur :** Victor (avec Claude Code)
**Statut :** Validé (cadrage initial)

---

## 1. Objectif

Construire un **assistant de trading crypto à but pédagogique et sans risque financier**.
L'outil récupère des données de marché, calcule des indicateurs techniques, génère
des signaux d'achat/vente, et permet de **tester** ces signaux de deux façons :

1. **Backtesting** — rejouer une stratégie sur des données historiques.
2. **Paper trading** — simuler des trades en temps réel avec un portefeuille fictif.

> ⚠️ **Aucune exécution d'ordre réel dans cette version.** Aucune clé API privée,
> aucun argent réel n'est manipulé. L'architecture est conçue pour pouvoir ajouter
> l'exécution réelle plus tard, comme un module séparé, sans réécrire l'existant.

### Public visé
Victor, débutant. L'outil doit être simple à lancer, lisible, et favoriser
l'apprentissage (graphes, explications, valeurs d'indicateurs visibles).

---

## 2. Périmètre (scope)

### Inclus
- Récupération de données OHLCV crypto via `ccxt` (données **publiques** Binance).
- Calcul d'indicateurs : **RSI, SMA, EMA, MACD, Bollinger Bands**.
- Détection de tendance simple (haussière / baissière / neutre).
- Stratégies générant des **signaux** (achat = +1, vente = -1, neutre = 0).
- **Backtesting** d'une stratégie sur l'historique avec métriques de performance.
- **Paper trading** : portefeuille fictif, suivi des positions et du P&L simulé.
- Calcul de **risque/récompense** et de **taille de position**.
- **Dashboard Streamlit** pour visualiser prix, indicateurs et résultats.
- **CLI** minimal pour lancer une analyse rapide.
- Cache local des données (CSV/SQLite) pour éviter de retélécharger.
- Tests unitaires (priorité : les indicateurs).

### Exclu (YAGNI — volontairement reporté)
- ❌ Exécution d'ordres réels sur un exchange.
- ❌ Modèles IA/ML avancés (LSTM, Prophet) — peu fiables, complexes pour débuter.
- ❌ Notifications (Telegram, email) — pourront être ajoutées plus tard.
- ❌ Marchés actions/forex — on se concentre sur la crypto d'abord.
- ❌ Optimisation de paramètres automatique (Grid Search).

Ces éléments ne sont pas abandonnés : l'architecture les rend ajoutables plus tard.

---

## 3. Architecture

### Principe directeur
Chaque module a **une seule responsabilité** et communique via des interfaces
claires. Le cœur du système est la notion de **signal** : une stratégie transforme
des données + indicateurs en signaux. Le backtest et le paper trading **consomment
ces mêmes signaux**. Le jour où l'on voudra trader pour de vrai, ce sera un nouveau
consommateur des mêmes signaux — rien à réécrire.

```
Données (OHLCV) ──> Indicateurs ──> Stratégie ──> Signaux ──┬──> Backtest
                                                            ├──> Paper trading
                                                            └──> (futur) Exécution réelle
```

### Structure des fichiers

```
trading-assistant/
├── core/
│   ├── market_data.py     # Récupération + cache des données OHLCV (ccxt)
│   ├── indicators.py      # RSI, SMA, EMA, MACD, Bollinger Bands
│   ├── strategy.py        # Stratégies -> colonne "signal" (+1/0/-1)
│   ├── backtest.py        # Rejoue une stratégie sur l'historique + métriques
│   ├── paper_trading.py   # Portefeuille fictif, positions, P&L simulé
│   └── risk.py            # Risk/reward ratio, taille de position
├── utils/
│   ├── config.py          # Paramètres (symbole, timeframe, capital de départ)
│   └── logger.py          # Journalisation simple
├── data/                  # Cache local (CSV / SQLite) — gitignored
├── tests/
│   ├── test_indicators.py
│   ├── test_strategy.py
│   └── test_backtest.py
├── dashboard.py           # Interface Streamlit
├── main.py                # Point d'entrée CLI
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 4. Composants (détail)

### `core/market_data.py`
- **Rôle :** fournir un DataFrame OHLCV propre (timestamp, open, high, low, close, volume).
- **Interface :** `fetch_ohlcv(symbol, timeframe='1d', limit=500) -> pd.DataFrame`.
- **Dépend de :** `ccxt`, `pandas`. Données **publiques** (aucune clé requise).
- **Cache :** sauvegarde/relit depuis `data/` pour éviter de retélécharger.

### `core/indicators.py`
- **Rôle :** fonctions pures qui ajoutent des colonnes d'indicateurs à un DataFrame.
- **Interface :** `add_rsi(df, window=14)`, `add_sma(df, window)`, `add_ema(df, window)`,
  `add_macd(df)`, `add_bollinger(df, window=20)`.
- **Dépend de :** `pandas`, `numpy` uniquement. Aucune dépendance réseau → facile à tester.

### `core/strategy.py`
- **Rôle :** transformer données + indicateurs en une colonne `signal` (+1 achat,
  -1 vente, 0 neutre).
- **Interface :** `class Strategy` avec `generate_signals(df) -> pd.DataFrame`.
  Au moins une stratégie d'exemple : **RSI + croisement de moyennes**.
- **Dépend de :** `indicators.py`.

### `core/backtest.py`
- **Rôle :** rejouer les signaux sur l'historique et mesurer la performance.
- **Interface :** `backtest(df_with_signals, capital_initial) -> BacktestResult`.
- **Métriques :** rendement total, nombre de trades, **win rate**, profit factor,
  drawdown maximal, courbe de capital (equity curve).

### `core/paper_trading.py`
- **Rôle :** simuler un portefeuille fictif en consommant des signaux, tour par tour.
- **Interface :** `class PaperPortfolio` (`buy`, `sell`, `update`, `summary`).
- **État :** cash fictif, position courante, historique des trades. Aucun argent réel.

### `core/risk.py`
- **Rôle :** outils de gestion du risque.
- **Interface :** `risk_reward_ratio(entry, stop, target)`,
  `position_size(capital, risk_pct, entry, stop)`.

### `dashboard.py` (Streamlit)
- Sélection du symbole et du timeframe.
- Graphe des prix + moyennes + Bollinger.
- Valeur courante des indicateurs (RSI, MACD) avec alertes (ex. RSI > 70 = surachat).
- Bouton « Backtester » affichant les métriques + equity curve.

### `main.py` (CLI)
- Commande simple : analyser un symbole et afficher le dernier signal + indicateurs.

---

## 5. Flux de données (exemple : backtest)

1. `market_data.fetch_ohlcv("BTC/USDT", "1d")` → DataFrame OHLCV (depuis cache si dispo).
2. `indicators.add_*` → colonnes RSI, SMA, MACD, Bollinger ajoutées.
3. `strategy.generate_signals(df)` → colonne `signal`.
4. `backtest(df, capital=1000)` → métriques + equity curve.
5. Affichage : CLI (texte) ou Streamlit (graphes).

---

## 6. Gestion des erreurs

- **Réseau / API indisponible :** message clair + repli sur le cache local si présent.
- **Symbole/timeframe invalide :** validation en amont, message explicite.
- **Données insuffisantes** (ex. moins de N bougies pour un indicateur) : avertir, ne pas planter.
- **Division par zéro** (RSI sans pertes, etc.) : géré dans les calculs d'indicateurs.

---

## 7. Stratégie de test

- **TDD sur les indicateurs** : valeurs connues vérifiées à la main (le cœur de la fiabilité).
- Tests sur `strategy.py` : signaux corrects pour des cas simples construits à la main.
- Tests sur `backtest.py` : sur une mini-série, le P&L et le win rate sont corrects.
- `market_data.py` : peu testé en réseau ; on teste la logique de cache avec des données fixtures.

---

## 8. Dépendances (`requirements.txt` prévisionnel)

```
ccxt          # données crypto
pandas        # manipulation de données
numpy         # calculs
streamlit     # dashboard
pytest        # tests
```

(Pas de `ta-lib` : installation pénible sous Windows. On code les indicateurs à la main,
c'est aussi plus pédagogique.)

---

## 9. Évolutions futures possibles

- Ajout d'un module `live_trading.py` consommant les mêmes signaux (avec garde-fous,
  clés API, confirmations) — **uniquement quand Victor sera à l'aise**.
- Notifications Telegram/email sur signal.
- Stratégies supplémentaires et comparaison.
- Support actions (`yfinance`) et forex.
- Modèles prédictifs avancés (optionnel).
