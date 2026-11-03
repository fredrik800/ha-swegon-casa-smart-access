"""Persistent estimated afterheater energy consumption for each CASA unit.

Energy is estimated from the previous valid afterheater percentage and the
configured rated heater power. Samples are typically 30 seconds apart.
Long gaps are deliberately not integrated, avoiding fabricated consumption
when Home Assistant or the Swegon unit is offline.
"""

import asyncio
import logging
import math
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, ID_AFTERHEATER_PERCENT

_LOGGER = logging.getLogger(__name__)

BUCKET_SECONDS = 300  # Five-minute bins for rolling-window history.
WINDOW_SECONDS = 30 * 24 * 60 * 60
MAX_SAMPLE_GAP_SECONDS = 120
SAVE_INTERVAL_SECONDS = 300


def energy_updated_event(entry_id: str) -> str:
    """Signal an explicit reset of the energy counters."""
    return f"{DOMAIN}_{entry_id}_energy_updated"


class SwegonCasaEnergyTracker:
    """Per-unit persistent kWh accumulator and rolling 30-day history."""

    def __init__(
        self, hass: HomeAssistant, entry_id: str, heater_watts: int
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.heater_watts = max(0, int(heater_watts))
        self.store = Store(hass, 1, f"{DOMAIN}_energy_{entry_id}")
        self.total_kwh = 0.0
        self.buckets: dict[int, float] = {}
        self._last_timestamp: float | None = None
        self._last_percent: float | None = None
        self._last_save_at = time.time()
        self._save_task: asyncio.Task[None] | None = None

    async def async_load(self) -> None:
        """Restore saved counters; never restore an old power sample."""
        try:
            data = await self.store.async_load()
            if not isinstance(data, dict):
                return
            total = float(data.get("total_kwh", 0))
            if math.isfinite(total) and total >= 0:
                self.total_kwh = total
            entries = data.get("buckets", [])
            if isinstance(entries, list):
                for item in entries:
                    try:
                        timestamp, energy = item
                        timestamp = int(timestamp)
                        energy = float(energy)
                        if math.isfinite(energy) and energy >= 0:
                            self.buckets[timestamp] = energy
                    except (TypeError, ValueError):
                        continue
            self._prune(time.time())
        except (TypeError, ValueError, OSError):
            _LOGGER.exception("Unable to restore Swegon energy counters for %s", self.entry_id)

    def process_reading(
        self, data: dict[str, Any], now: float | None = None
    ) -> None:
        """Integrate the last known heater output over a valid sample interval."""
        timestamp = time.time() if now is None else now
        try:
            percent = float(data[ID_AFTERHEATER_PERCENT])
            if not math.isfinite(percent) or not 0 <= percent <= 100:
                raise ValueError("Invalid heater percentage")
        except (KeyError, TypeError, ValueError):
            self._last_timestamp = None
            self._last_percent = None
            return

        if self.heater_watts <= 0:
            self._last_timestamp = None
            self._last_percent = None
            return

        if self._last_timestamp is not None and self._last_percent is not None:
            elapsed = timestamp - self._last_timestamp
            if 0 < elapsed <= MAX_SAMPLE_GAP_SECONDS:
                power_kw = self.heater_watts * self._last_percent / 100_000
                self._add_interval(self._last_timestamp, timestamp, power_kw)

        self._last_timestamp = timestamp
        self._last_percent = percent
        self._prune(timestamp)

        if (
            timestamp - self._last_save_at >= SAVE_INTERVAL_SECONDS
            and (self._save_task is None or self._save_task.done())
        ):
            self._last_save_at = timestamp
            self._save_task = self.hass.async_create_task(
                self.store.async_save(self._serialize())
            )

    def _add_interval(self, start: float, end: float, power_kw: float) -> None:
        """Split sampled energy at five-minute UTC bucket boundaries."""
        if power_kw <= 0:
            return
        self.total_kwh += power_kw * (end - start) / 3600
        cursor = start
        while cursor < end:
            bucket = int(cursor // BUCKET_SECONDS)
            duration = min(end, (bucket + 1) * BUCKET_SECONDS) - cursor
            if duration <= 0:
                break
            self.buckets[bucket] = (
                self.buckets.get(bucket, 0.0) + power_kw * duration / 3600
            )
            cursor += duration

    def _prune(self, now: float) -> None:
        """Discard buckets fully outside the rolling 30-day window."""
        cutoff = now - WINDOW_SECONDS
        for bucket in list(self.buckets):
            if (bucket + 1) * BUCKET_SECONDS <= cutoff:
                del self.buckets[bucket]

    def last_30_days_kwh(self, now: float | None = None) -> float:
        """Return a rolling 30-day estimate, interpolating the edge bucket."""
        timestamp = time.time() if now is None else now
        self._prune(timestamp)
        cutoff = timestamp - WINDOW_SECONDS
        result = 0.0
        for bucket, energy in self.buckets.items():
            start = bucket * BUCKET_SECONDS
            end = start + BUCKET_SECONDS
            overlap = max(0.0, min(end, timestamp) - max(start, cutoff))
            if overlap:
                result += energy * overlap / BUCKET_SECONDS
        return result

    def _serialize(self) -> dict[str, Any]:
        """Produce a compact, versioned storage payload."""
        return {
            "total_kwh": round(self.total_kwh, 9),
            "buckets": [
                [bucket, round(energy, 10)]
                for bucket, energy in sorted(self.buckets.items())
            ],
        }

    async def async_save(self) -> None:
        """Flush any pending write and persist the latest values."""
        if self._save_task is not None and not self._save_task.done():
            await self._save_task
        await self.store.async_save(self._serialize())
        self._last_save_at = time.time()

    async def async_reset(self) -> None:
        """Clear both the lifetime counter and the entire rolling history."""
        if self._save_task is not None and not self._save_task.done():
            await self._save_task
        self.total_kwh = 0.0
        self.buckets.clear()
        self._last_timestamp = None
        self._last_percent = None
        await self.store.async_save(self._serialize())
        self._last_save_at = time.time()
        self.hass.bus.async_fire(energy_updated_event(self.entry_id))
