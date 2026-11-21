"""Switch to control the night mode of an LG soundbar."""

from typing import Any, override

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LGSoundbarConfigEntry, TemescalBridge
from .const import DOMAIN, KEY_NIGHT_MODE, MSG_SETTING_VIEW_INFO


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: LGSoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switch from a config entry created in the integrations UI."""
    bridge = config_entry.runtime_data
    unique_id = config_entry.unique_id or config_entry.entry_id
    async_add_entities([LGNightModeSwitch(bridge, unique_id)])


class LGNightModeSwitch(SwitchEntity):
    """Representation of the night mode of an LG soundbar."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "night_mode"
    _attr_icon = "mdi:weather-night"

    def __init__(self, bridge: TemescalBridge, unique_id: str) -> None:
        """Initialize the switch."""
        self._bridge = bridge
        self._night_mode: bool | None = None
        self._attr_unique_id = f"{unique_id}_night_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)}, name=bridge.host
        )

    @override
    async def async_added_to_hass(self) -> None:
        """Register the callback after hass is ready for it."""
        self._bridge.add_listener(self.handle_event)
        # The initial state responses arrive while connecting, before the
        # entities are registered, so ask the device to report again.
        await self.hass.async_add_executor_job(self._bridge.refresh)

    @override
    async def async_will_remove_from_hass(self) -> None:
        """Unregister the callback before hass tears the entity down."""
        self._bridge.remove_listener(self.handle_event)

    def handle_event(self, response: dict[str, Any]) -> None:
        """Handle responses from the speakers."""
        data = response.get("data") or {}
        if response["msg"] == MSG_SETTING_VIEW_INFO and KEY_NIGHT_MODE in data:
            self._night_mode = data[KEY_NIGHT_MODE]
            self.schedule_update_ha_state()

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether night mode is enabled."""
        return self._night_mode

    @override
    def turn_on(self, **kwargs: Any) -> None:
        """Enable night mode."""
        self._bridge.set_night_mode(True)

    @override
    def turn_off(self, **kwargs: Any) -> None:
        """Disable night mode."""
        self._bridge.set_night_mode(False)
