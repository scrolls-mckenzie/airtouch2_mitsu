"""AirTouch 2 component to control AirTouch 2 Climate Device."""
from __future__ import annotations

from airtouch2.at2 import At2Client
from .Airtouch2ClimateEntity import Airtouch2ClimateEntity
from .const import DOMAIN

import logging
from pprint import pprint

from homeassistant.components.climate import ClimateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Airtouch 2."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    airtouch2_client: At2Client = data["client"]
    entities: list[ClimateEntity] = [
        Airtouch2ClimateEntity(ac) for ac in airtouch2_client.aircons_by_id.values()
    ]

    if entities:
        async_add_entities(entities)