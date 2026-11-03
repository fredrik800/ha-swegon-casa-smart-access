"""Offline unit tests for estimated afterheater energy tracking."""

import asyncio
import math
import time
from typing import Any

import pytest

from custom_components.swegon_casa import energy


class FakeBus:
    def __init__(self) -> None:
        self.events: list[str] = []

    def async_fire(self, event: str) -> None:
        self.events.append(event)


class FakeHass:
    def __init__(self) -> None:
        self.bus = FakeBus()

    def async_create_task(self, coroutine: Any) -> asyncio.Task[Any]:
        return asyncio.create_task(coroutine)


@pytest.fixture
def fake_storage(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace HA Store with an in-memory store that survives tracker reloads."""
    saved: dict[str, Any] = {}

    class FakeStore:
        def __init__(self, hass: Any, version: int, key: str) -> None:
            self.key = key

        async def async_load(self) -> Any:
            return saved.get(self.key)

        async def async_save(self, payload: Any) -> None:
            saved[self.key] = payload

    monkeypatch.setattr(energy, "Store", FakeStore)
    return saved


@pytest.mark.asyncio
async def test_hour_at_half_power_is_0_4_kwh(fake_storage: Any) -> None:
    """800 W at 50 percent for an hour is 0.4 kWh."""
    hass = FakeHass()
    tracker = energy.SwegonCasaEnergyTracker(hass, "r5", 800)
    now = time.time()
    for index in range(121):
        tracker.process_reading({"38": 50}, now=now + 30 * index)
    assert tracker.total_kwh == pytest.approx(0.4)
    assert tracker.last_30_days_kwh(now=now + 3600) == pytest.approx(0.4)
    await tracker.async_save()


@pytest.mark.asyncio
async def test_long_gaps_and_missing_samples_are_not_estimated(
    fake_storage: Any,
) -> None:
    """Skip long outages and missing API ID 38."""
    tracker = energy.SwegonCasaEnergyTracker(FakeHass(), "r5", 800)
    now = time.time()
    tracker.process_reading({"38": 50}, now=now)
    tracker.process_reading({"38": 50}, now=now + 30)
    expected = 0.4 * 30 / 3600
    tracker.process_reading({"38": 50}, now=now + 330)
    tracker.process_reading({}, now=now + 360)
    tracker.process_reading({"38": 50}, now=now + 390)
    assert tracker.total_kwh == pytest.approx(expected)
    tracker.process_reading({"38": 50}, now=now + 420)
    assert tracker.total_kwh == pytest.approx(expected * 2)
    await tracker.async_save()


@pytest.mark.asyncio
async def test_rolling_window_counts_current_partial_bucket(
    fake_storage: Any,
) -> None:
    """Current 5-minute bucket is not multiplied by its partial elapsed fraction."""
    tracker = energy.SwegonCasaEnergyTracker(FakeHass(), "r5", 800)
    now = math.floor(time.time() / 300) * 300 + 150
    tracker._add_interval(now - 30, now, 0.4)
    assert tracker.last_30_days_kwh(now=now) == pytest.approx(0.4 * 30 / 3600)

    cutoff = now - energy.WINDOW_SECONDS
    oldest_bucket = math.floor(cutoff / 300)
    tracker.buckets[oldest_bucket] = 1.0
    expected_fraction = ((oldest_bucket + 1) * 300 - cutoff) / 300
    assert tracker.last_30_days_kwh(now=now) == pytest.approx(
        0.4 * 30 / 3600 + expected_fraction
    )


@pytest.mark.asyncio
async def test_persistence_reset_and_per_unit_isolation(fake_storage: Any) -> None:
    """A reset removes both values for R5 without touching R2."""
    hass = FakeHass()
    r5 = energy.SwegonCasaEnergyTracker(hass, "r5", 800)
    r2 = energy.SwegonCasaEnergyTracker(hass, "r2", 400)
    now = time.time()
    for tracker in (r5, r2):
        tracker.process_reading({"38": 100}, now=now)
        tracker.process_reading({"38": 100}, now=now + 30)
        await tracker.async_save()

    reloaded = energy.SwegonCasaEnergyTracker(hass, "r5", 800)
    await reloaded.async_load()
    assert reloaded.total_kwh == pytest.approx(0.8 * 30 / 3600)
    assert reloaded._last_timestamp is None  # No backfill across restarts.
    await reloaded.async_reset()
    assert reloaded.total_kwh == 0
    assert reloaded.last_30_days_kwh() == 0
    assert fake_storage["swegon_casa_energy_r5"]["buckets"] == []
    assert "swegon_casa_r5_energy_updated" in hass.bus.events

    other = energy.SwegonCasaEnergyTracker(hass, "r2", 400)
    await other.async_load()
    assert other.total_kwh == pytest.approx(0.4 * 30 / 3600)


@pytest.mark.asyncio
async def test_no_wattage_no_energy(fake_storage: Any) -> None:
    """Without rated heater power, no energy is invented."""
    tracker = energy.SwegonCasaEnergyTracker(FakeHass(), "unknown", 0)
    now = time.time()
    tracker.process_reading({"38": 100}, now=now)
    tracker.process_reading({"38": 100}, now=now + 30)
    assert tracker.total_kwh == 0
    await tracker.async_save()
