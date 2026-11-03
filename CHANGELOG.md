# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2026-11-03

### Added
- Persistent per-unit afterheater energy total (kWh), suitable for HA Energy Dashboard.
- Rolling last-30-days estimated afterheater energy (kWh), stored in five-minute bins.
- Per-unit button to reset both the lifetime total and all 30-day history.

### Behavior
- Estimates energy from the previous afterheater percentage, configured heater
  wattage, and elapsed time between valid samples (typically 30 seconds).
- Counter and rolling history survive Home Assistant restarts and integration reloads.
- Gaps longer than 120 seconds are skipped rather than estimated; downtime is not counted.
- History starts when v1.0.3 is installed and cannot recover past energy use.
- Automatic saves every five minutes, plus saves on clean integration unload.
- Changing the configured wattage affects future energy only; reset both counters
  if you want to restart after recalibration.
- The 30-day rolling window is approximated with five-minute UTC bins.

## [1.0.2] - 2026-11-03

### Added
- Afterheater output percentage (local API ID 38), plus estimated power in watts using per-unit rated wattage.
- Estimated supply/exhaust fan RPM based on fan percentage and per-unit calibration; rounded to nearest 100 RPM.
- Per-unit options for IP address, heater rated power, and fan RPM calibration (0 disables uncalibrated sensors).

### Fixed
- Preserve v1.0.1 absolute-humidity scaling (API ID 23 / 10).
- Isolate data events by Home Assistant config entry so R2/R5 readings cannot cross-contaminate.
- Stop polling tasks on unload/reload.
- Remove misleading RPM unit and long-term measurement state class from unverified API ID 27.
  Existing Home Assistant long-term statistics for that old sensor may require manual cleanup.

### Notes
- Heater W and fan RPM are estimates, not direct electrical or tachometer measurements.
- ID 38 was verified on CASA R5; confirm its behavior on other models.
- Existing entity unique IDs are retained.

## [1.0.1] - 2026-11-01

### Fixed
- Separate per-unit updates for multiple Swegon CASA devices.
- Correct absolute humidity scaling to g/m³.

## [1.0.0] - 2025-10-19

### Added
- Initial release of Swegon Casa Smart Access Module Home Assistant integration

### Features
- **Climate Entity**: HVAC control with current temperature display
- **Sensor Entities**: 
  - Supply, return, and outdoor temperature sensors
  - Humidity percentage and absolute humidity (g/m³)
  - Fan speed monitoring
  - Boost countdown
- **Select Entities**:
  - Climate mode control
  - Auto humidity control mode
  - Cooling mode selection
  - Fireplace mode toggle
  - Travel mode toggle
- **Number Entities**:
  - Temperature setpoint adjustment
  - Travel mode temperature drop control

### Dependencies
- aiohttp >= 3.8.0
- websockets >= 11.0
- homeassistant >= 2023.12.0
- python-dotenv >= 1.0.0

### Code Quality
- Black code formatting
- isort import sorting
- Ruff linting
- mypy type checking
- Comprehensive test suite

---

For more information, see the [README](README.md).
