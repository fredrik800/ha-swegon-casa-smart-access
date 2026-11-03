"""Swegon Casa client for Home Assistant."""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class SwegonCasaClient:
    """Client for Swegon Casa local API."""

    def __init__(self, host: str, username: str, password: str):
        """Initialize the client."""
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"https://{host}"
        self.cookies: dict[str, str] = {}
        self.session: aiohttp.ClientSession | None = None

        self._measurement_callback: Callable[[str, Any], None] | None = None
        self._mode_callback: Callable[[str, Any], None] | None = None
        self._setting_callback: Callable[[str, Any], None] | None = None

    def set_session(self, session: aiohttp.ClientSession) -> None:
        """Set the aiohttp session."""
        self.session = session

    def on_measurement(self, callback: Callable[[str, Any], None]) -> None:
        """Register measurement callback."""
        self._measurement_callback = callback

    def on_mode(self, callback: Callable[[str, Any], None]) -> None:
        """Register mode callback."""
        self._mode_callback = callback

    def on_setting(self, callback: Callable[[str, Any], None]) -> None:
        """Register setting callback."""
        self._setting_callback = callback

    async def _make_request(
        self, path: str, data: str | None = None
    ) -> tuple[int, Any] | None:
        """Make HTTP request to the device."""
        if not self.session:
            _LOGGER.error("Session not set")
            return None

        max_retries = 2
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}{path}"
                _LOGGER.debug("Making request to %s (attempt %d)", url, attempt + 1)

                async with self.session.post(
                    url,
                    ssl=False,
                    data=data,
                    cookies=self.cookies,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    for cookie_name, cookie_value in response.cookies.items():
                        self.cookies[cookie_name] = cookie_value.value

                    try:
                        json_data = await response.json()
                        return response.status, json_data
                    except aiohttp.ContentTypeError:
                        return response.status, None
            except aiohttp.ServerDisconnectedError as err:
                _LOGGER.debug("Server disconnected (attempt %d): %s", attempt + 1, err)
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    _LOGGER.error("Request error after retries: %s", err)
                    return None
            except Exception as err:
                _LOGGER.error("Request error: %s", err)
                return None

        return None

    async def login(self) -> bool:
        """Login to the device."""
        try:
            result = await self._make_request(
                "/handle_login", f"username={self.username}&password={self.password}"
            )

            if result is None:
                return False

            status, _ = result
            if status != 200:
                _LOGGER.error("Login failed with status %s", status)
                return False

            _LOGGER.debug("Login successful")
            return True

        except Exception as err:
            _LOGGER.error("Login error: %s", err)
            return False

    async def fetch_data(self) -> dict[str, Any] | None:
        """Fetch sensor data from the device."""
        try:
            success = await self.login()
            if not success:
                return None

            payload = self._get_read_payload()
            result = await self._make_request("/api", json.dumps(payload))

            if result is None:
                _LOGGER.error("Fetch failed: no response")
                return None

            status, json_res = result
            if status != 200:
                _LOGGER.error("Fetch failed with status %s", status)
                return None

            result_obj = json_res.get("result", {}).get("objects", [])
            sorted_data = {}

            for item in result_obj:
                item_id = item.get("id")
                properties = item.get("properties", {})
                measurement = properties.get("85")

                if measurement:
                    value = measurement.get("value")
                    if value is not None:
                        sorted_data[item_id] = value

            return sorted_data

        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            return None

    async def set_value(self, object_id: str, value: int) -> bool:
        """Set a value on the device."""
        try:
            success = await self.login()
            if not success:
                return False

            payload = self._get_write_payload(object_id, value)
            result = await self._make_request("/api", json.dumps(payload))

            if result is None:
                _LOGGER.error("Set value failed: no response")
                return False

            status, json_res = result
            if status != 200:
                _LOGGER.error("Set value failed with status %s", status)
                return False

            _LOGGER.debug("Set value response: %s", json_res)
            return True

        except Exception as err:
            _LOGGER.error("Error setting value: %s", err)
            return False

    def _get_read_payload(self, read_ids: list[str] | None = None) -> dict[str, Any]:
        """Create read payload."""
        if read_ids is None:
            read_ids = [
                "17",
                "18",
                "19",
                "22",
                "23",
                "27",
                "28",
                "29",
                "31",
                "38",  # Afterheater output percent
                "121",
                "163",
                "111",
                "153",
                "154",
                "200",
                "201",
            ]

        objects = [
            {"id": id, "properties": {"85": {}}, "device": 255} for id in read_ids
        ]

        return {
            "jsonrpc": "2.0",
            "id": 0,
            "params": {
                "objects": objects,
            },
            "method": "read",
        }

    async def set_climate_mode(self, _: int, new_mode: int) -> bool:
        """Set climate mode."""
        return await self.set_value("111", new_mode)

    def _get_write_payload(self, write_id: str, write_value: int) -> dict[str, Any]:
        """Create write payload."""
        return {
            "jsonrpc": "2.0",
            "id": 0,
            "params": {
                "objects": [
                    {
                        "id": write_id,
                        "properties": {
                            "85": {
                                "value": int(write_value),
                            },
                        },
                        "device": 255,
                    },
                ],
            },
            "method": "write",
        }
