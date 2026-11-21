"""The lg_soundbar component."""

from collections.abc import Callable
import logging
from typing import Any

import temescal

from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.exceptions import ConfigEntryNotReady

from .config_flow import test_connect

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SWITCH]

type LGSoundbarConfigEntry = ConfigEntry[TemescalBridge]


class TemescalBridge:
    """Connection to an LG soundbar shared by the entities of a config entry.

    temescal supports a single event callback, so the entities of an entry
    share this bridge and events are fanned out to its listeners.
    """

    def __init__(self, host: str, port: int) -> None:
        """Initialize the bridge and connect to the device."""
        self._listeners: list[Callable[[dict[str, Any]], None]] = []
        self._device = temescal.temescal(host, port=port, callback=self.handle_event)
        self._device.get_product_info()
        self._device.get_mac_info()
        self.refresh()

    @property
    def device(self) -> temescal.temescal:
        """Return the connected device."""
        return self._device

    def refresh(self) -> None:
        """Ask the device to report its current state."""
        self._device.get_eq()
        self._device.get_info()
        self._device.get_func()
        self._device.get_settings()
        self._device.get_play()

    def set_night_mode(self, enable: bool) -> None:
        """Set the night mode of the device."""
        self._device.set_night_mode(enable)

    def add_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        """Add a listener that receives all events from the device."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        """Remove a listener that was added before."""
        self._listeners.remove(listener)

    def handle_event(self, response: dict[str, Any]) -> None:
        """Fan out an event from the device to all listeners."""
        for listener in list(self._listeners):
            listener(response)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: LGSoundbarConfigEntry
) -> None:
    """Set up platform from a ConfigEntry."""
    # Verify the device is reachable with the given
    # config before setting up the platform
    try:
        await hass.async_add_executor_job(
            test_connect, entry.data[CONF_HOST], entry.data[CONF_PORT]
        )
    except ConnectionError as err:
        raise ConfigEntryNotReady from err

    try:
        bridge = await hass.async_add_executor_job(
            TemescalBridge, entry.data[CONF_HOST], entry.data[CONF_PORT]
        )
    except OSError as err:
        raise ConfigEntryNotReady from err
    entry.runtime_data = bridge

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: LGSoundbarConfigEntry
) -> None:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
