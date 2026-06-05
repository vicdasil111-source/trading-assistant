# 📈 Trading Assistant

Assistant de trading **crypto** à but **pédagogique**. Il récupère des données de
marché, calcule des indicateurs techniques, génère des signaux d'achat/vente, et
permet de les **tester** par backtesting et paper trading.

> ⚠️ **Important — aucun argent réel.**
> Cette version ne passe **aucun ordre réel** et ne demande **aucune clé API privée**.
> Tout est analyse et simulation. Rien ici n'est un conseil financier. Le trading
> comporte un risque réel de perte ; la performance passée ne garantit pas l'avenir.

---

## ✨ Ce que fait l'outil

- 📥 **Données de marché** crypto via [`ccxt`](https://github.com/ccxt/ccxt) (Binance, données publiques), avec cache local.
- 📊 **Indicateurs** : RSI, SMA, EMA, MACD, Bandes de Bollinger, détection de tendance.
- 🧠 **Stratégies** qui produisent des signaux (`rsi_sma`, `ema_cross`).
- ⏪ **Backtesting** sur l'historique (rendement, win rate, profit factor, drawdown).
- 🧪 **Paper trading** : portefeuille fictif pour s'entraîner sans risque.
- 🛡️ **Gestion du risque** : ratio risque/récompense, taille de position.
- 🖥️ **Dashboard Streamlit** + **CLI**.

---

## 🚀 Installation

Prérequis : **Python 3.10+**.

```bash
# 1. Se placer dans le dossier du projet
cd trading-assistant

# 2. (Recommandé) créer un environnement virtuel
python -m venv .venv
# Windows (PowerShell) :
.venv\Scripts\Activate.ps1
# macOS / Linux :
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

---

## 🕹️ Utilisation

### En ligne de commande (CLI)

```bash
# Analyse rapide d'un actif (derniers indicateurs + dernier signal)
python main.py analyse --symbol BTC/USDT --timeframe 1d

# Backtester une stratégie
python main.py backtest --symbol ETH/USDT --strategy rsi_sma --capital 1000

# Stratégie de croisement de moyennes
python main.py backtest --strategy ema_cross
```

Options principales : `--symbol`, `--timeframe` (`1m`,`1h`,`4h`,`1d`,`1w`),
`--limit`, `--strategy` (`rsi_sma` ou `ema_cross`), `--capital`.

### Dashboard (navigateur)

```bash
streamlit run dashboard.py
```

Puis choisis un actif et une stratégie dans la barre latérale et clique **Analyser**.

---

## 🧱 Structure du projet

```
trading-assistant/
├── core/
│   ├── market_data.py   # Récupération + cache des données (ccxt)
│   ├── indicators.py    # RSI, SMA, EMA, MACD, Bollinger
│   ├── strategy.py      # Stratégies -> signaux (+1/0/-1)
│   ├── backtest.py      # Backtest + métriques
│   ├── paper_trading.py # Portefeuille fictif
│   └── risk.py          # Risque/récompense, taille de position
├── utils/
│   ├── config.py        # Paramètres centraux
│   └── logger.py        # Journalisation
├── tests/               # Tests (pytest)
├── data/                # Cache local (créé automatiquement)
├── dashboard.py         # Interface Streamlit
├── main.py              # CLI
└── requirements.txt
```

**Idée centrale :** une *stratégie* transforme les données en *signaux*. Le backtest
et le paper trading consomment ces mêmes signaux. Pour ajouter du trading réel un
jour, il suffirait d'un nouveau module qui consomme les mêmes signaux — sans rien
réécrire.

---

## 🧪 Lancer les tests

```bash
pytest -q
```

Les tests des indicateurs et du backtest ne nécessitent **pas** de connexion internet.

---

## ➕ Créer ta propre stratégie

Hérite de `Strategy` et implémente `generate_signals` (dans `core/strategy.py`) :

```python
class MaStrategie(Strategy):
    name = "ma_strategie"

    def generate_signals(self, df):
        df = df.copy()
        df["signal"] = 0
        # ... ta logique : mets +1 (achat) ou -1 (vente) ...
        return df
```

Puis ajoute-la au dictionnaire `AVAILABLE_STRATEGIES`.

---

## 🗺️ Évolutions possibles (plus tard)

- Notifications (Telegram / email) sur signal.
- Frais et slippage dans le backtest pour plus de réalisme.
- Support des actions (`yfinance`) et du forex.
- Exécution réelle d'ordres — **uniquement avec garde-fous et en connaissance de cause**.

---

## ⚖️ Avertissement

Projet éducatif. Ce logiciel est fourni « tel quel », sans garantie. Il ne constitue
pas un conseil en investissement. N'investis jamais d'argent que tu ne peux pas te
permettre de perdre.
