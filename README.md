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
- 📊 **Indicateurs** : RSI, SMA, EMA, MACD, Bollinger, **ATR**, **Stochastique**, **OBV**, tendance.
- 🎛️ **Panneau d'options** : choix d'actif, intervalle, indicateurs réglables, affichage modulable.
- 🌙☀️ **Thème clair / sombre** (bascule instantanée), sous-graphes RSI/MACD/Stochastique, volume.
- ⬇️ **Exports CSV** (données + indicateurs, trades du backtest) et **glossaire** intégré.
- 👤 **Comptes utilisateurs** (inscription / connexion, mots de passe **hachés** PBKDF2, session
  persistante par jeton) avec **watchlist** et préférences par utilisateur.
- 🧮 **Outils de risque** (taille de position, risque/récompense) et **comparateur multi-actifs**.
- 🧠 **4 stratégies** qui produisent des signaux : `rsi_sma`, `ema_cross`, `macd_cross`, `bollinger`.
- ⏪ **Backtesting** sur l'historique, avec **frais de transaction**, **benchmark Buy & Hold**,
  win rate, profit factor, **ratio de Sharpe** et drawdown.
- ⚖️ **Comparaison** de toutes les stratégies d'un coup (`compare`).
- 🧪 **Paper trading** : portefeuille fictif pour s'entraîner sans risque.
- 🛡️ **Gestion du risque** : ratio risque/récompense, taille de position.
- 🔔 **Alertes** (console, + Telegram optionnel).
- ⚙️ **Auto-optimisation** des stratégies, avec détection du **sur-apprentissage**.
- 🤖 **Pilote automatique** : portefeuille fictif autonome qui décide seul.
- 🧠 **Machine Learning** : prédiction de tendance (scikit-learn), évaluée honnêtement.
- 🧪 **Testnet Binance** (argent fictif) pour apprendre l'exécution sans risque.
- 🖥️ **Site multi-pages Streamlit** (graphe en **chandelles**) + **CLI**.

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
# Analyse rapide d'un actif (derniers indicateurs + dernier signal + alertes)
python main.py analyse --symbol BTC/USDT --timeframe 1d

# Backtester une stratégie (avec 0,1 % de frais par transaction)
python main.py backtest --symbol ETH/USDT --strategy rsi_sma --capital 1000 --fee 0.1

# Comparer TOUTES les stratégies sur le même actif
python main.py compare --symbol BTC/USDT --fee 0.1
```

Options principales : `--symbol`, `--timeframe` (`1m`,`1h`,`4h`,`1d`,`1w`),
`--limit`, `--strategy` (`rsi_sma`, `ema_cross`, `macd_cross`, `bollinger`),
`--capital`, `--fee` (frais en %), `--notify` (envoi Telegram, voir plus bas).

### 🔔 Alertes Telegram (optionnel)

Par défaut, les alertes s'affichent dans la console. Pour les recevoir aussi sur
Telegram, définis deux variables d'environnement (aucune clé n'est stockée dans le code) :

```powershell
$env:TELEGRAM_BOT_TOKEN = "ton_token"   # créé via @BotFather
$env:TELEGRAM_CHAT_ID   = "ton_chat_id"
python main.py analyse --symbol BTC/USDT --notify
```

### Le site (navigateur)

```bash
streamlit run dashboard.py
```

Un site **multi-pages** s'ouvre dans le navigateur, avec dans la barre latérale :

| Page | Ce qu'elle fait |
|---|---|
| 📈 **Analyse** (accueil) | Chandelles + volume + signaux, indicateurs réglables, backtest |
| ⚙️ **Optimisation** | Le bot règle ses stratégies tout seul + détection du sur-apprentissage |
| 🤖 **Pilote auto** | Portefeuille fictif autonome qui décide seul (état sauvegardé) |
| 🧠 **Machine Learning** | Un modèle prédit la tendance, évalué honnêtement |
| 👤 **Compte** | Inscription / connexion (mots de passe hachés, session persistante) |
| ⭐ **Watchlist** | Liste de suivi personnelle (prix, RSI, tendance, signal) — nécessite un compte |
| 🧮 **Outils** | Calculateur de taille de position et de ratio risque/récompense |
| 📊 **Comparateur** | Performances de plusieurs actifs sur une même base 100 |

### Pilote automatique en boucle (CLI)

```bash
python autopilot_runner.py --symbol BTC/USDT --timeframe 1h --strategy rsi_sma
python autopilot_runner.py --once   # un seul pas
```

Le pilote tourne en simulation (argent fictif). `Ctrl+C` pour arrêter ; l'état est sauvegardé.

### Exécution sur testnet (apprentissage, argent fictif)

L'exécution d'ordres réels **autonome n'est pas supportée** (trop risqué). Pour apprendre
l'exécution sans risque, le module `core/execution.py` parle au **testnet Binance**
(argent fictif). Tout est en `dry_run` par défaut. Clés gratuites sur
<https://testnet.binance.vision/> :

```powershell
$env:BINANCE_TESTNET_API_KEY = "..."
$env:BINANCE_TESTNET_SECRET  = "..."
```

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
│   ├── risk.py          # Risque/récompense, taille de position
│   ├── optimizer.py     # Auto-optimisation (train/test, anti sur-apprentissage)
│   ├── ml_strategy.py   # Stratégie Machine Learning (scikit-learn)
│   ├── autopilot.py     # Pilote automatique (paper trading persistant)
│   └── execution.py     # Exécution testnet Binance (argent fictif, garde-fous)
├── utils/
│   ├── config.py        # Paramètres centraux
│   ├── logger.py        # Journalisation
│   └── notifications.py # Alertes (console + Telegram optionnel)
├── pages/               # Pages du site (Optimisation, Pilote auto, ML)
├── tests/               # Tests (pytest)
├── data/                # Cache + état du pilote (créé automatiquement)
├── dashboard.py         # Site Streamlit (page d'accueil : Analyse)
├── autopilot_runner.py  # Pilote automatique en boucle (CLI)
├── main.py              # CLI (analyse, backtest, compare)
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

## 🌍 Publier le site (mise en ligne gratuite)

Le plus simple pour une app Streamlit : **Streamlit Community Cloud** (gratuit). Il
déploie directement depuis un dépôt GitHub et donne une URL publique `…streamlit.app`.

1. **Mettre le code sur GitHub** (dépôt public ou privé) :
   ```bash
   git remote add origin https://github.com/<ton-pseudo>/trading-assistant.git
   git push -u origin main
   ```
2. **Déployer** : aller sur <https://share.streamlit.io>, se connecter avec GitHub,
   cliquer **Create app**, choisir le dépôt, mettre `dashboard.py` comme *Main file
   path*, puis **Deploy**.
3. C'est en ligne. Le déploiement se met à jour automatiquement à chaque `git push`.

Notes :
- `requirements.txt` est déjà prêt ; Streamlit Cloud installe les dépendances seul.
- Si l'API Binance est bloquée sur l'hébergeur, le site se rabat automatiquement sur
  les **données d'exemple embarquées** (`data/samples/`) : il fonctionne quand même.
- Ne mets **jamais** de clés API dans le dépôt (le `.gitignore` protège déjà `.env`).

## ⚖️ Avertissement

Projet éducatif. Ce logiciel est fourni « tel quel », sans garantie. Il ne constitue
pas un conseil en investissement. N'investis jamais d'argent que tu ne peux pas te
permettre de perdre.
