"""Test the lg_soundbar switch."""

from unittest.mock import MagicMock

import pytest
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchService
from homeassistant.const import TargetKey
from homeassistant.core import HomeAssistant

from . import find_update_callback, setup_integration

ENTITY_ID = "switch.127_0_0_1_night_mode"


def send_night_mode(callback: MagicMock, enabled: bool) -> None:
    """Report the given night mode state via the callback."""
    callback({"msg": "SETTING_VIEW_INFO", "data": {"b_night_mode": enabled}})


async def test_state_is_unknown_before_the_device_reports(
    hass: HomeAssistant,
    mock_temescal: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that the switch is unknown until a night mode state is reported."""
    await setup_integration(hass, mock_config_entry)

    assert hass.states.get(ENTITY_ID).state == "unknown"


@pytest.mark.parametrize(
    ("enabled", "expected_state"),
    [
        pytest.param(True, "on", id="on"),
        pytest.param(False, "off", id="off"),
    ],
)
async def test_state_follows_a_reported_night_mode(
    hass: HomeAssistant,
    mock_temescal: MagicMock,
    mock_config_entry: MockConfigEntry,
    enabled: bool,
    expected_state: str,
) -> None:
    """Test that a reported night mode state decides the state of the switch."""
    await setup_integration(hass, mock_config_entry)

    send_night_mode(find_update_callback(mock_temescal), enabled)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == expected_state


async def test_turning_on(
    hass: HomeAssistant,
    mock_temescal: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that turning the switch on enables night mode on the device."""
    await setup_integration(hass, mock_config_entry)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SwitchService.TURN_ON,
        {TargetKey.ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_temescal.return_value.set_night_mode.assert_called_once_with(True)


async def test_turning_off(
    hass: HomeAssistant,
    mock_temescal: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that turning the switch off disables night mode on the device."""
    await setup_integration(hass, mock_config_entry)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SwitchService.TURN_OFF,
        {TargetKey.ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_temescal.return_value.set_night_mode.assert_called_once_with(False)
