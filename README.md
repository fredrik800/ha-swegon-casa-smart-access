# Swegon Casa Home Assistant Integration

> This repository is a fork of [TMschar/ha-swegon-casa-smart-access](https://github.com/TMschar/ha-swegon-casa-smart-access). Version **1.0.2** adds experimental calculated sensors and per-unit configuration. Thanks to the original author; this fork is not an official Swegon integration.

## Fork v1.0.3: afterheater energy tracking

The integration now adds three entities for each configured CASA unit:

- **FTX Total Energy Consumption** (kWh): persistent lifetime estimated energy.
  This is a `total_increasing` sensor usable in the Home Assistant Energy Dashboard.
- **FTX Last 30 Days Energy** (kWh): rolling 30-day estimate, stored in
  five-minute bins and updated as the window moves.
- **FTX Reset Energy Consumption**: resets *both* counters and the full
  30-day history for the selected unit only.

Energy is calculated from the last valid afterheater percentage multiplied by
the configured rated heater wattage and the elapsed time between readings.
It is **an estimate**, not metered electrical energy. Gaps over two minutes,
including HA outages, are not extrapolated. Counters are saved to HA storage
every five minutes and on a clean integration unload; sudden power loss may
lose up to approximately five minutes of measurements. History begins when
this feature is installed; older consumption cannot be reconstructed.
A change to heater wattage applies only to future readings. Reset both
counters if you recalibrate and want a fresh baseline.

## Fork v1.0.2: afterheater and estimated fan RPM

- **Afterheater control (%)** from local API object 38 (verified on R5).
- **Estimated heater power (W)**: afterheater percentage multiplied by rated heater wattage (e.g. R2 400 W, R5 800 W).
- **Estimated supply/exhaust fan RPM**, calculated from the respective fan percentages and user-supplied RPM at 100% and rounded to 100 RPM steps. These are **not measured RPM**.
- **Options per device**: change IP address and calibrate rated heater watts and fan RPM independently for each Swegon unit.
- Preserves the **v1.0.1** multi-unit isolation and absolute humidity scaling fix.
- Unverified API object 27 is no longer labelled as RPM; Home Assistant may prompt to clean up historical statistics for this legacy sensor.

### Install this fork via HACS

Add `https://github.com/fredrik800/ha-swegon-casa-smart-access` as a **custom repository** of type **Integration** in HACS, then install the fork and restart Home Assistant. Avoid installing the upstream integration alongside this fork because both use the same `swegon_casa` domain. Back up `/config/custom_components/swegon_casa/` and your HA configuration before switching.

After installation, open **Settings > Devices & services > Swegon Casa > Configure** on each unit and set its wattage/RPM calibration. A value of 0 makes the corresponding calculated sensor unavailable until calibrated.



[![GitHub Release](https://img.shields.io/github/release/TMschar/ha-swegon-casa-smart?style=flat-square)](https://github.com/TMschar/ha-swegon-casa-smart/releases)
[![GitHub Downloads](https://img.shields.io/github/downloads/TMschar/ha-swegon-casa-smart/total?style=flat-square)](https://github.com/TMschar/ha-swegon-casa-smart)
[![HACS Badge](https://img.shields.io/badge/HACS-default-41BDF5?style=flat-square)](https://github.com/hacs/integration)

A comprehensive Home Assistant integration for Swegon Casa air handling units. Control your HVAC system, monitor indoor and outdoor air quality, and manage humidity settings directly from Home Assistant.

## Features

**HVAC Control**
- Climate mode selection (Away, Home, Boost, Travel, Off, Fireplace)
- Temperature setpoint adjustment
- Travel mode with temperature drop control
- Fireplace mode toggle

**Monitoring**
- Supply, return, and outdoor temperature sensors
- Humidity percentage and absolute humidity tracking
- Fan speed monitoring (supply and exhaust)
- Boost countdown tracking

**Controls**
- Auto humidity control mode selection
- Summer night cooling mode
- Humidity target adjustment
- Cooling mode control

## Installation

### Via HACS (Recommended)
1. Go to **Settings** → **Devices & Services** → **HACS**
2. Click the **Explore & Download Repositories** button
3. Search for "Swegon Casa Smart Access"
4. Click **Download**
5. Restart Home Assistant

### Manual Installation
1. Download the latest release from [GitHub Releases](https://github.com/TMschar/ha-swegon-casa-smart-access/releases)
2. Extract to `~/.homeassistant/custom_components/swegon_casa`
3. Restart Home Assistant

## Setup

1. Go to **Settings** → **Devices & Services** → **Create Integration**
2. Search for "Swegon Casa Smart Access"
3. Enter your Swegon Casa Smart Access credentials
   You should have these from the package with the Smart Access Module, as a sticker
4. Complete the setup

## Supported Entities

### Climate
- Main HVAC entity with current temperature and mode control

### Sensors
- Supply, return, and outdoor temperatures
- Humidity (% and g/m³)
- Fan speeds and boost countdown

### Selects
- Climate mode
- Auto humidity control
- Cooling mode
- Fireplace mode toggle
- Travel mode toggle

### Numbers
- Temperature setpoint
- Travel mode temperature drop

## Requirements

- Home Assistant 2023.12+
- Python 3.11+
- Swegon Casa Smart Access module with network connectivity

It does not have to be connected to the cloud!

## Troubleshooting

**Integration fails to add:**
- Verify credentials are correct
- Verify the IP is correct (connect to it via web browser)

**Entities not updating:**
- Check Home Assistant logs
- Verify device is still online
- Restart the integration

## Architecture

The integration uses a clean async architecture:
- `client.py`: HTTP/WebSocket client for Swegon API
- `config_flow.py`: Setup wizard and authentication
- `climate.py`: HVAC climate entity
- `sensor.py`: Temperature and humidity sensors
- `select.py`: Mode and control selections
- `number.py`: Numeric controls (temperature setpoints)
- `const.py`: Constants and mappings

## Development

### Setup Development Environment
```bash
uv sync --all-groups
```

### Run Quality Checks
```bash
bash lint.sh
```

### Run Tests
```bash
uv run pytest tests/
```

## License

Apache License

## Support

For issues, feature requests, or questions:
- [GitHub Issues](https://github.com/TMschar/ha-swegon-casa-smart-access/issues)
- Documentation: [Integration Guide](./custom_components/swegon_casa/README.md)

---

*This integration is not affiliated with Swegon or Home Assistant.*
