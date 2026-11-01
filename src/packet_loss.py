"""Packet loss calculations.

Packet loss = share of test messages (ping probes) that got no reply in time.
Because ping needs the reply to come back, this loss covers BOTH directions;
it is not the same as the one-way loss metric of RFC 7680.
"""
from typing import Dict, Optional

from .models import ProbeStats


def calculate_loss_pct(sent: int, received: int) -> Optional[float]:
    """Return loss as a percentage (0-100), or None if nothing was sent."""
    if sent <= 0:
        return None
    return round(100.0 * (sent - received) / sent, 1)


def loss_summary(stats: ProbeStats) -> Dict[str, object]:
    """Sent / received / lost / percentage, ready for a table."""
    return {
        "target": stats.target,
        "sent": stats.sent,
        "received": stats.received,
        "lost": stats.lost,
        "loss_pct": stats.loss_pct,
    }


def is_loss_significant(stats: Optional[ProbeStats], warn_pct: float, min_lost: int) -> bool:
    """True if loss is at/above the warning limit AND at least `min_lost` probes were lost.

    The minimum count stops one single lost probe from looking like a fault.
    """
    if stats is None or not stats.available or stats.loss_pct is None:
        return False
    return stats.lost >= min_lost and stats.loss_pct >= warn_pct
