"""Shared data structures. All hourly keys are UTC datetimes at the START of the hour."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

UTC = timezone.utc
MM_PER_IN = 25.4


def hour_floor(t: datetime) -> datetime:
    return t.astimezone(UTC).replace(minute=0, second=0, microsecond=0)


def hours(start: datetime, n: int) -> list[datetime]:
    return [start + timedelta(hours=i) for i in range(n)]


@dataclass
class Series:
    """One source's hourly forecast, in inches per hour."""
    key: str                      # short id, e.g. "nws", "hrrr", "ens", "radar"
    label: str                    # human label
    issued: datetime | None       # model run / product time, if known
    url: str = ""
    values: dict[datetime, float] = field(default_factory=dict)       # best-guess amount
    members: dict[datetime, list[float]] = field(default_factory=dict)  # ensemble/nowcast samples
    prob: dict[datetime, float] = field(default_factory=dict)         # optional direct P(any) e.g. NWS PoP
    note: str = ""
    smoothed: bool = False        # True when hourly values are spread from multi-hour totals

    def p_exceed(self, t: datetime, thresh: float) -> float | None:
        m = self.members.get(t)
        if not m:
            return None
        return sum(1 for x in m if x >= thresh) / len(m)


@dataclass
class SourceStatus:
    name: str
    ok: bool
    detail: str
    url: str = ""
    time: datetime | None = None
