# ⚖️ Mentions légales, risques & conformité

> **Information générale — pas un conseil.** Ce document informe les utilisateurs.
> Il ne constitue pas un conseil en investissement, juridique ou fiscal. En cas de
> doute, consulte un professionnel agréé.

## 1. Nature du projet

**Trading Assistant** est un logiciel **éducatif** d'analyse de marché et de
simulation. Il peut, **à la demande explicite de l'utilisateur et sous sa seule
responsabilité**, passer des ordres sur un compte d'exchange via API. Il s'utilise
**pour son propre compte uniquement**.

## 2. Avertissement sur les risques

- Le trading de crypto-actifs est **hautement risqué** : perte totale possible.
- L'**automatisation** (autopilote) peut générer des pertes **sans intervention humaine**.
- La **performance passée ne préjuge pas** des résultats futurs.
- Bugs, latences, pannes d'exchange ou de réseau peuvent entraîner des ordres
  ratés, partiels ou en double.
- **N'engage que des sommes que tu peux te permettre de perdre.**

## 3. Absence de conseil

Les signaux, backtests, optimisations et automatisations sont des **outils
techniques**. Ils ne constituent **pas** une recommandation personnalisée ni un
**conseil en investissement** (activité réglementée non fournie par ce projet).

## 4. Cadre réglementaire (France / UE)

- Un **usage personnel**, pour son propre compte, est en principe **licite**.
- **Fournir un service sur crypto-actifs à des tiers** (exécution, conservation,
  courtage, gestion…) relève du règlement européen **MiCA** et nécessite un
  agrément **CASP / PSAN** délivré, en France, par l'**AMF**.
- La période transitoire française **prend fin le 1ᵉʳ juillet 2026**.
- **Ne propose pas ce bot comme service** à autrui sans t'être renseigné auprès
  de l'AMF et, le cas échéant, obtenu les agréments requis.

Réf. : Autorité des marchés financiers (AMF), dossier MiCA —
<https://www.amf-france.org/en/news-publications/depth/mica>.

## 5. Fiscalité (France)

- Les plus-values de cession de crypto par un particulier sont **imposables**
  (prélèvement forfaitaire unique « flat tax » de **30 %**, option barème possible).
- Obligation de **déclarer les comptes d'actifs numériques à l'étranger**
  (formulaire **3916-bis**).
- **Conserve l'historique** de toutes tes opérations. Vérifie les règles à jour
  sur **impots.gouv.fr** ou auprès d'un expert-comptable.

## 6. Sécurité des clés API

- Utilise des clés **« trading » uniquement, sans droit de retrait**.
- Restreins-les par **adresse IP** si possible.
- Stocke-les en **variables d'environnement**, jamais dans le code ni sur GitHub.
- **N'entre jamais** de clés réelles sur un déploiement **public partagé** : le
  trading réel n'est déverrouillé qu'en **auto-hébergement**
  (`I_UNDERSTAND_REAL_MONEY_RISK=yes` + tes clés).

## 7. Données personnelles (RGPD)

- Comptes : identifiant, e-mail facultatif, **mot de passe haché** (PBKDF2 + sel),
  et listes personnelles (watchlist, portefeuille, alertes, préférences).
- Les mots de passe ne sont **jamais** stockés en clair.
- Droit de **suppression** : ouvre une *issue* sur le dépôt pour toute demande.
- Aucune **clé API** n'est stockée par l'application.

## 8. Absence de garantie

Logiciel fourni « **en l'état** », sans garantie d'aucune sorte. Les auteurs ne
sauraient être tenus responsables de pertes financières, directes ou indirectes,
liées à son utilisation.
