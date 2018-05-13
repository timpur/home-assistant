"""HA Homie Seneos module"""

import logging

from homie.tools.constants import PROP_VALUE
from homie.tools.helpers import check_node_has_prop
from homeassistant.helpers.entity import (Entity, async_generate_entity_id)
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.homie import (
    DOMAIN,
    KEY_HOMIE_DISCOVERED,
    KEY_HOMIE_ENTITY_ID,
    PlatformBindError,
    HomieNode
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass: HomeAssistantType, _, async_add_entities, discovery_info=None):
    """Set up the Homie sensor."""
    entity_id = discovery_info[KEY_HOMIE_ENTITY_ID]
    homie_node = hass.data[DOMAIN][KEY_HOMIE_DISCOVERED][entity_id]
    if homie_node is None:
        raise PlatformBindError()
    check_node_has_prop('Sensor', homie_node, PROP_VALUE)

    _LOGGER.info(f"Setting up Homie Sensor: {entity_id}")
    async_add_entities([HomieSensor(hass, entity_id, homie_node)])


# TODO: add expiry of state
class HomieSensor(Entity):
    """Implementation of a Homie Sensor."""

    def __init__(self, hass: HomeAssistantType, entity_id: str, homie_node: HomieNode):
        """Initialize Homie Sensor."""
        self._id = entity_id
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, entity_id, hass=hass)
        self._node = homie_node
        self._node.device.add_attribute_listener(self._on_change, '_online')
        self._node.get_property(
            PROP_VALUE).add_attribute_listener(self._on_change)

    def _on_change(self, obj, name, pre, value):
        self.async_schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the Homie Sensor."""
        return self._id

    @property
    def state(self):
        """Return the state of the Homie Sensor."""
        return self._node.get_property(PROP_VALUE).state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'unit'

    @property
    def should_poll(self):
        return False
