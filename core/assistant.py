"""
Assistant pédagogique : répond à des questions sur l'app, les indicateurs,
les stratégies, le risque et le cadre légal — SANS jamais donner de conseil
en investissement.

100 % local : pas d'API, pas de dépendance, pas de clé. Un petit moteur
d'intentions par mots-clés sur une base de connaissances écrite à la main.
Déterministe → facile à tester. Si un jour tu veux brancher un vrai LLM, il
suffira de remplacer `answer()`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

DISCLAIMER = "_Rappel : information pédagogique, pas un conseil en investissement._"


def _norm(text: str) -> str:
    """Minuscule + sans accents, pour comparer les mots-clés simplement."""
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


@dataclass(frozen=True)
class Intent:
    name: str
    keywords: tuple[str, ...]
    answer: str


# Les mots-clés sont déjà normalisés (minuscule, sans accent).
KB: tuple[Intent, ...] = (
    Intent("salutation", ("bonjour", "salut", "coucou", "hello", "hey", "yo"),
           "Bonjour 👋 Je suis l'assistant du site. Je peux t'expliquer les "
           "indicateurs (RSI, MACD…), les stratégies, le backtest, le risque, le "
           "trading réel et le cadre légal. Pose ta question, ou choisis un exemple."),
    Intent("capacites", ("que sais", "que peux", "tu peux faire", "aide", "help",
                         "tu sers a quoi", "comment tu marches"),
           "Je réponds à des questions sur : **les indicateurs** (RSI, SMA/EMA, "
           "MACD, Bollinger, Stochastique…), **les stratégies**, **le backtest** "
           "(Sharpe, drawdown, Buy & Hold), **le risque et les garde-fous**, **le "
           "trading réel** (clés, testnet, autopilote) et **la loi / les impôts**. "
           "Je ne donne pas de conseil d'achat : je t'aide à comprendre."),
    Intent("projet", ("a quoi sert", "ca sert a quoi", "le projet", "cette appli",
                      "cette application", "presente", "but du site", "c est quoi le site"),
           "**Trading Assistant** est un outil **pédagogique** pour comprendre les "
           "marchés crypto : il récupère des données réelles, calcule des "
           "indicateurs, génère des signaux et permet de les **tester** (backtest, "
           "paper trading, auto-optimisation, machine learning) **sans risquer "
           "d'argent**. Le but n'est pas de gagner de l'argent, c'est de "
           "**comprendre** pourquoi une stratégie marche ou échoue."),
    Intent("rsi", ("rsi", "surachat", "surachet", "survente", "survendu", "force relative"),
           "**RSI (Relative Strength Index)** : un indicateur de 0 à 100 qui mesure "
           "la force d'une tendance. Au-dessus de **70**, l'actif est dit "
           "« suracheté » (souvent monté vite) ; en dessous de **30**, « survendu ». "
           "Ce ne sont pas des ordres d'achat/vente : juste des repères de momentum.\n\n"
           + DISCLAIMER),
    Intent("moyennes", ("moyenne mobile", "moyennes", "sma", "ema", "moyenne"),
           "**Moyennes mobiles (SMA / EMA)** : elles lissent le prix pour révéler la "
           "tendance. La **SMA** est une moyenne simple, l'**EMA** donne plus de "
           "poids aux prix récents (elle réagit plus vite). Quand une moyenne courte "
           "passe au-dessus d'une longue, on parle de croisement haussier."),
    Intent("macd", ("macd", "convergence divergence"),
           "**MACD** : la différence entre deux moyennes exponentielles, avec une "
           "ligne de signal. Le croisement des deux lignes, et l'histogramme qui "
           "change de signe, signalent un changement de **momentum**.\n\n" + DISCLAIMER),
    Intent("bollinger", ("bollinger", "bandes de"),
           "**Bandes de Bollinger** : une moyenne mobile entourée de deux bandes à "
           "± N écarts-types. Les bandes s'écartent quand la **volatilité** monte et "
           "se resserrent quand elle baisse. Le prix qui touche une bande n'est pas "
           "un signal en soi."),
    Intent("stochastique", ("stochastique", "stoch"),
           "**Stochastique** : situe la clôture dans la fourchette haut/bas récente, "
           "de 0 à 100. Au-dessus de **80** = haut de la fourchette, en dessous de "
           "**20** = bas. Utile pour repérer des excès, à confirmer avec d'autres "
           "indicateurs."),
    Intent("atr", ("atr", "average true range"),
           "**ATR (Average True Range)** : mesure la **volatilité** moyenne (l'ampleur "
           "des variations), pas la direction. Très utile pour dimensionner un "
           "stop-loss : plus l'ATR est grand, plus le marché bouge."),
    Intent("obv", ("obv", "on balance volume", "volume cumule"),
           "**OBV (On-Balance Volume)** : additionne le volume les jours de hausse et "
           "le retranche les jours de baisse. Une divergence entre l'OBV et le prix "
           "peut indiquer un essoufflement de la tendance."),
    Intent("backtest", ("backtest", "tester une strategie", "sur le passe",
                        "historique strategie"),
           "**Backtest** : on rejoue une stratégie sur des données passées (frais "
           "inclus) pour voir ce qu'elle aurait donné. ⚠️ Une bonne performance "
           "passée **ne garantit rien** pour l'avenir (attention au sur-apprentissage : "
           "une stratégie peut être « réglée » pour coller au passé et échouer ensuite)."),
    Intent("sharpe", ("sharpe",),
           "**Ratio de Sharpe** : le rendement rapporté au risque pris (la "
           "volatilité). Plus il est élevé, mieux c'est : un gros rendement très "
           "instable peut avoir un Sharpe médiocre."),
    Intent("drawdown", ("drawdown", "pire baisse", "perte maximale"),
           "**Drawdown maximum** : la pire baisse depuis un sommet, en %. Il dit "
           "combien tu aurais « encaissé » dans le creux. Un drawdown énorme rend "
           "une stratégie difficile à tenir psychologiquement."),
    Intent("buyhold", ("buy and hold", "buy & hold", "acheter et garder", "b&h", "bh"),
           "**Buy & Hold** : acheter et garder sans rien faire. C'est la **référence** "
           "à battre : si une stratégie active fait moins bien que le Buy & Hold (frais "
           "compris), elle ne vaut pas la complexité."),
    Intent("strategies", ("strategie", "strategies", "rsi_sma", "ema_cross",
                          "macd_cross", "breakout", "quelle approche"),
           "Le site propose 5 stratégies : **rsi_sma** (RSI + tendance par moyennes), "
           "**ema_cross** (croisement d'EMA), **macd_cross** (croisement MACD), "
           "**bollinger** (retour vers la moyenne) et **breakout** (cassure de plus "
           "haut/bas). Compare-les sur la page **Analyse** : aucune n'est « la "
           "meilleure » dans l'absolu.\n\n" + DISCLAIMER),
    Intent("risque", ("risque", "dangereux", "perdre mon argent", "danger", "perte"),
           "Le trading crypto est **très risqué** : tu peux perdre **tout** ton "
           "capital, vite. L'automatisation peut enchaîner des pertes sans toi. "
           "C'est pour ça que ce site est **simulé par défaut**, avec des garde-fous "
           "pour le réel. Règle d'or : **n'engage que ce que tu peux perdre**."),
    Intent("gardefous", ("garde-fou", "garde fou", "kill switch", "coupe-circuit",
                         "coupe circuit", "plafond", "arret d'urgence", "limite de"),
           "Les **garde-fous** protègent le trading réel : plafond par ordre, perte "
           "max par jour, nombre d'ordres max par jour, et un **coupe-circuit** "
           "(bouton ARRÊT D'URGENCE) qui bloque tout d'un clic. Un ordre dont la "
           "valeur est inconnue est **refusé** par sécurité."),
    Intent("reel", ("trading reel", "argent reel", "vrai argent", "activer le reel",
                    "passer en reel", "money reel", "investir reellement"),
           "Le **trading réel** existe mais il est **verrouillé sur le site public** "
           "(aucune clé n'y est présente — on ne touche jamais à l'argent des autres, "
           "et le proposer en service exigerait un agrément AMF). Pour l'activer, "
           "**héberge l'app chez toi** avec tes clés Binance et "
           "`I_UNDERSTAND_REAL_MONEY_RISK=yes`. Commence petit, en testnet d'abord. "
           "Détails sur la page **Aide & FAQ**."),
    Intent("cles", ("cle api", "cles api", "api key", "cle binance", "mes cles"),
           "Utilise des clés API **« trading uniquement, SANS droit de retrait »**, "
           "idéalement restreintes par adresse IP. Stocke-les en **variables "
           "d'environnement**, **jamais** dans le code, sur GitHub, ni sur un site "
           "public partagé. L'app ne stocke aucune clé."),
    Intent("testnet", ("testnet", "argent fictif", "reseau de test", "simule",
                       "simulation", "sans risque"),
           "Le **testnet** Binance te laisse passer de vrais ordres avec de l'**argent "
           "fictif** : parfait pour t'entraîner sans rien risquer. Crée des clés "
           "gratuites sur testnet.binance.vision, puis va sur la page **Trading "
           "testnet**."),
    Intent("autopilote", ("autopilote", "pilote auto", "automatique", "tout seul",
                          "robot", "bot achete"),
           "L'**autopilote** calcule un signal de stratégie et **agit seul**, sans te "
           "redemander. C'est le mode **le plus risqué** : à n'utiliser qu'en "
           "simulation/testnet tant que tu n'es pas sûr de toi. En réel, il reste "
           "bridé par les garde-fous et le coupe-circuit."),
    Intent("legal", ("legal", "la loi", "amf", "mica", "casp", "psan", "autorise",
                     "reglement", "legalite"),
           "Pour un **usage personnel**, c'est en principe **licite**. En revanche, "
           "**proposer ce bot comme service à d'autres** relève du règlement européen "
           "**MiCA** et nécessite un agrément **CASP/PSAN** (via l'**AMF** en France ; "
           "fin de la période transitoire le **1ᵉʳ juillet 2026**). Ce n'est pas un "
           "conseil juridique — renseigne-toi auprès de l'AMF."),
    Intent("fiscalite", ("impot", "impots", "fiscalite", "taxe", "flat tax",
                         "plus-value", "plus value", "declarer", "3916"),
           "En France, les **plus-values** de cession de crypto sont **imposables** "
           "(flat tax de **30 %**, option barème possible), et il faut **déclarer les "
           "comptes à l'étranger** (formulaire **3916-bis**). Garde l'historique de "
           "tes opérations. Vérifie sur impots.gouv.fr — ce n'est pas un conseil fiscal."),
    Intent("rgpd", ("rgpd", "donnees personnelles", "mot de passe", "vie privee",
                    "supprimer mon compte", "confidentialite"),
           "Côté **données** : ton mot de passe est **haché** (jamais en clair), et "
           "l'app ne stocke **aucune clé API**. Tu peux demander la **suppression** "
           "de tes données (ouvre une issue sur le dépôt). Voir **Mentions légales**."),
    Intent("demarrer", ("comment utiliser", "par ou commencer", "comment ca marche",
                        "utiliser le site", "debuter", "je commence", "premier pas"),
           "Pour commencer : sur l'**accueil**, regarde le **marché en direct** et "
           "clique une tuile pour analyser un actif. Dans la barre latérale de la "
           "page **Analyse**, choisis un actif + une stratégie, puis **Analyser** "
           "pour voir indicateurs, signaux et backtest. Explore ensuite **Pilote "
           "auto** et **Machine Learning**."),
    Intent("conseil", ("dois-je acheter", "dois je acheter", "quoi acheter",
                       "donne moi un conseil", "ca va monter", "va monter",
                       "va baisser", "prediction du prix", "je dois investir",
                       "c'est le moment", "bon investissement", "quel actif acheter"),
           "Je ne peux pas te dire quoi acheter ni prédire les prix : ce **ne serait "
           "pas fiable** et ce **n'est pas un conseil en investissement**. Ce que je "
           "peux faire : t'aider à **analyser** un actif (indicateurs, tendance) et à "
           "**backtester** une stratégie pour que **tu** décides en connaissance de "
           "cause. Personne ne sait où ira le prix.\n\n" + DISCLAIMER),
)

_FALLBACK = (
    "Je n'ai pas de réponse toute prête à ça 🤔. Essaie une question sur : "
    "**RSI, MACD, Bollinger, stratégies, backtest, Sharpe, drawdown, risque, "
    "garde-fous, trading réel, testnet, autopilote, légal, impôts**. "
    "Pour le reste, la page **Aide & FAQ** est très complète."
)

SUGGESTIONS: tuple[str, ...] = (
    "Prix du Bitcoin ?",
    "Les dernières actus crypto ?",
    "C'est quoi le RSI ?",
    "Comment activer le trading réel ?",
    "Dois-je acheter du Bitcoin ?",
    "Par où commencer ?",
)


def _matches(keyword: str, question_norm: str) -> bool:
    """Mot-clé court (<= 4 car.) → match sur frontière de mot (évite « ema » dans
    « demain ») ; mot-clé plus long → sous-chaîne (tolère les pluriels/variantes)."""
    if len(keyword) <= 4:
        return re.search(r"\b" + re.escape(keyword) + r"\b", question_norm) is not None
    return keyword in question_norm


def _score(question_norm: str, intent: Intent) -> int:
    return sum(1 for kw in intent.keywords if _matches(kw, question_norm))


# --- Capacités « en direct » (prix + actualités via internet) ----------------
# Noms d'actifs reconnus -> paire. Permet « prix du bitcoin » -> BTC/USDT.
COINS: dict[str, str] = {
    "btc": "BTC/USDT", "bitcoin": "BTC/USDT",
    "eth": "ETH/USDT", "ethereum": "ETH/USDT", "ether": "ETH/USDT",
    "sol": "SOL/USDT", "solana": "SOL/USDT",
    "bnb": "BNB/USDT", "binance coin": "BNB/USDT",
    "xrp": "XRP/USDT", "ripple": "XRP/USDT",
    "doge": "DOGE/USDT", "dogecoin": "DOGE/USDT",
    "ada": "ADA/USDT", "cardano": "ADA/USDT",
    "avax": "AVAX/USDT", "avalanche": "AVAX/USDT",
    "link": "LINK/USDT", "chainlink": "LINK/USDT",
    "dot": "DOT/USDT", "polkadot": "DOT/USDT",
    "ltc": "LTC/USDT", "litecoin": "LTC/USDT",
    "trx": "TRX/USDT", "tron": "TRX/USDT",
}

_PRICE_KW = ("prix", "cours", "combien vaut", "combien coute", "valeur de",
             "cote de", "ca vaut", "vaut combien")
_NEWS_KW = ("news", "actu", "actus", "actualite", "actualites", "nouvelle",
            "nouvelles", "journal", "journaux", "quoi de neuf", "se passe",
            "derniere info", "dernieres infos", "headlines", "infos")


def _find_symbol(question_norm: str) -> str | None:
    for name, symbol in COINS.items():
        if _matches(name, question_norm):
            return symbol
    return None


def detect(question: str):
    """Détecte une demande « live ». Renvoie ('price', 'BTC/USDT'),
    ('news', None) ou (None, None). Pur → testable."""
    qn = _norm(question)
    if any(_matches(k, qn) for k in _NEWS_KW):
        return ("news", None)
    if any(_matches(k, qn) for k in _PRICE_KW):
        sym = _find_symbol(qn)
        if sym:
            return ("price", sym)
    return (None, None)


def respond(question: str, *, price_fn=None, news_fn=None) -> str:
    """Réponse « augmentée » : utilise des données en direct (prix, actualités)
    quand des fournisseurs sont passés ET que la question s'y prête ; sinon, se
    rabat sur la base de connaissances statique `answer()`.

    `price_fn(symbol) -> float` et `news_fn() -> list[dict(title, link, source)]`
    sont injectés par la page (qui gère le réseau) → ce module reste testable.
    """
    kind, arg = detect(question)

    if kind == "price" and price_fn is not None:
        try:
            prix = float(price_fn(arg))
        except Exception:
            return "Je n'arrive pas à récupérer le prix en direct là, réessaie dans un instant."
        base = arg.split("/")[0]
        return (f"💹 **{base}** vaut actuellement **{prix:,.2f} USDT** (prix en direct). "
                f"Pour l'analyser en détail, ouvre la page **Analyse**.\n\n" + DISCLAIMER)

    if kind == "news" and news_fn is not None:
        try:
            items = list(news_fn() or [])
        except Exception:
            items = []
        if items:
            lignes = "\n".join(
                f"- [{it['title']}]({it['link']})" + (f" — _{it['source']}_" if it.get("source") else "")
                for it in items[:6])
            return ("📰 **Dernières actualités crypto :**\n\n" + lignes
                    + "\n\nPlus de titres sur la page **Actualités**.\n\n" + DISCLAIMER)
        return "Je n'ai pas réussi à récupérer les actualités en direct là, réessaie plus tard."

    return answer(question)


def answer(question: str) -> str:
    """Renvoie la meilleure réponse (markdown) à une question libre."""
    if not question or not question.strip():
        return "Pose-moi une question 🙂 (ex. « C'est quoi le RSI ? »)."
    qn = _norm(question)
    best: Intent | None = None
    best_score = 0
    for intent in KB:
        s = _score(qn, intent)
        if s > best_score:
            best, best_score = intent, s
    if best is None or best_score == 0:
        return _FALLBACK
    return best.answer


def suggestions() -> list[str]:
    """Quelques questions d'exemple pour amorcer la conversation."""
    return list(SUGGESTIONS)
