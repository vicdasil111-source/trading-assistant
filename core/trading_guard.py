"""
Garde-fous pour l'exécution d'ordres — la pièce de sécurité du trading réel.

Philosophie : un débutant qui automatise des achats avec de l'argent réel peut
tout perdre très vite. Ce module impose des limites **dures**, vérifiées avant
chaque ordre réel :

  - taille maximale d'un ordre (en USDT),
  - perte cumulée maximale sur la journée,
  - nombre maximal d'ordres par jour,
  - un « coupe-circuit » (kill switch) : un simple fichier qui, s'il existe,
    bloque TOUT ordre réel immédiatement.

Tout est en stdlib (json + pathlib), testable hors-ligne, sans dépendance.
Les ordres en simulation (dry-run) et sur le testnet ne sont PAS bridés :
les garde-fous ne servent qu'à protéger l'argent réel.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path

from utils.config import DATA_DIR


class GuardrailError(RuntimeError):
    """Levée quand un garde-fou bloque un ordre réel."""


# --- Coupe-circuit (kill switch) -------------------------------------------
# Présence du fichier => plus aucun ordre réel n'est autorisé.
KILL_SWITCH_FILE = DATA_DIR / "KILL_SWITCH"


def kill_switch_active(path: Path | str | None = None) -> bool:
    return Path(path or KILL_SWITCH_FILE).exists()


def engage_kill_switch(reason: str = "", path: Path | str | None = None) -> None:
    """Active le coupe-circuit : aucun ordre réel ne passera tant qu'il est là."""
    p = Path(path or KILL_SWITCH_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    horodatage = _dt.datetime.now(_dt.timezone.utc).isoformat()
    p.write_text(f"{horodatage}\n{reason}\n", encoding="utf-8")


def release_kill_switch(path: Path | str | None = None) -> None:
    """Désactive le coupe-circuit (supprime le fichier s'il existe)."""
    p = Path(path or KILL_SWITCH_FILE)
    try:
        p.unlink()
    except FileNotFoundError:
        pass


# --- Limites de risque -----------------------------------------------------
@dataclass
class Guardrails:
    """Limites de sécurité pour le trading réel (valeurs prudentes par défaut)."""

    max_order_usdt: float = 50.0          # taille max d'un seul ordre
    daily_loss_limit_usdt: float = 100.0  # perte cumulée max sur la journée
    max_trades_per_day: int = 10          # nombre max d'ordres par jour

    def validate(self) -> None:
        if self.max_order_usdt <= 0:
            raise ValueError("max_order_usdt doit être > 0.")
        if self.daily_loss_limit_usdt <= 0:
            raise ValueError("daily_loss_limit_usdt doit être > 0.")
        if self.max_trades_per_day <= 0:
            raise ValueError("max_trades_per_day doit être > 0.")


def validate_order(
    guardrails: Guardrails,
    *,
    order_value_usdt: float,
    trades_today: int = 0,
    loss_today_usdt: float = 0.0,
    kill_switch: bool = False,
) -> None:
    """Vérifie qu'un ordre réel respecte les garde-fous. Lève GuardrailError sinon.

    On échoue « fermé » : si la valeur de l'ordre est inconnue (0 ou négative),
    on refuse — mieux vaut bloquer que laisser passer un ordre non maîtrisé.
    """
    if kill_switch:
        raise GuardrailError(
            "Coupe-circuit activé : tout trading réel est suspendu. "
            "Relâche-le explicitement pour réactiver."
        )
    if order_value_usdt <= 0:
        raise GuardrailError(
            "Valeur d'ordre inconnue ou nulle : refus par sécurité "
            "(impossible de vérifier le plafond par ordre)."
        )
    if order_value_usdt > guardrails.max_order_usdt:
        raise GuardrailError(
            f"Ordre de {order_value_usdt:.2f} USDT au-dessus du plafond "
            f"de {guardrails.max_order_usdt:.2f} USDT par ordre."
        )
    if trades_today >= guardrails.max_trades_per_day:
        raise GuardrailError(
            f"Limite de {guardrails.max_trades_per_day} ordres/jour atteinte "
            f"({trades_today} déjà passés aujourd'hui)."
        )
    if loss_today_usdt >= guardrails.daily_loss_limit_usdt:
        raise GuardrailError(
            f"Perte du jour ({loss_today_usdt:.2f} USDT) au-delà de la limite "
            f"de {guardrails.daily_loss_limit_usdt:.2f} USDT. Arrêt pour la journée."
        )


# --- Journal des ordres réels (pour les limites quotidiennes) --------------
def _today() -> str:
    return _dt.date.today().isoformat()


def _ledger_path(data_dir: Path | str | None = None) -> Path:
    return Path(data_dir or DATA_DIR) / "trade_ledger.json"


def _load_ledger(data_dir: Path | str | None = None) -> dict:
    p = _ledger_path(data_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def today_stats(data_dir: Path | str | None = None) -> dict:
    """Statistiques des ordres réels du jour : trades, notional, perte."""
    led = _load_ledger(data_dir)
    return led.get(_today(), {"trades": 0, "notional": 0.0, "loss": 0.0})


def record_trade(
    order_value_usdt: float,
    realized_pnl_usdt: float = 0.0,
    data_dir: Path | str | None = None,
) -> dict:
    """Enregistre un ordre réel exécuté (pour faire respecter les limites/jour)."""
    p = _ledger_path(data_dir)
    led = _load_ledger(data_dir)
    jour = led.setdefault(_today(), {"trades": 0, "notional": 0.0, "loss": 0.0})
    jour["trades"] = int(jour.get("trades", 0)) + 1
    jour["notional"] = float(jour.get("notional", 0.0)) + float(order_value_usdt)
    if realized_pnl_usdt < 0:
        jour["loss"] = float(jour.get("loss", 0.0)) + (-float(realized_pnl_usdt))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(led, indent=2), encoding="utf-8")
    return jour
