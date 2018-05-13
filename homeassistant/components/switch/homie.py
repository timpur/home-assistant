"""HA Homie Switch module"""

import logging

from homie.tools.constants import PROP_ON
from homie.tools.helpers import (
    check_node_has_prop,
    string_to_bool,
    bool_to_string
)
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.components.switch import (SwitchDevice, ENTITY_ID_FORMAT)
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
    """Set up the Homie Switch."""
    entity_id = discovery_info[KEY_HOMIE_ENTITY_ID]
    homie_node = hass.data[DOMAIN][KEY_HOMIE_DISCOVERED][entity_id]
    if homie_node is None:
        raise PlatformBindError()
    check_node_has_prop('Switch', homie_node, PROP_ON)

    _LOGGER.info(f"Setting up Homie Switch: {entity_id}")
    async_add_entities([HomieSwitch(hass, entity_id, homie_node)])


class HomieSwitch(SwitchDevice):
    """Implementation of a Homie Switch."""

    def __init__(self, hass: HomeAssistantType, entity_id: str, homie_node: HomieNode):
        """Initialize Homie Switch."""
        self._id = entity_id
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, entity_id, hass=hass)
        self._node = homie_node
        self._node.device.add_attribute_listener(self._on_change, '_online')
        self._node.get_property(
            PROP_ON).add_attribute_listener(self._on_change)

    def _on_change(self, obj, name, pre, value):
        self.async_schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the Homie Switch."""
        return self._id

    @property
    def is_on(self):
        """Returns true if the Homie Switch is on."""
        return string_to_bool(self._node.get_property(PROP_ON).state)

    async def async_turn_on(self, **kwargs):
        """Turn the device on.

        This method is a coroutine.
        """
        self._node.get_property(PROP_ON).set_state(bool_to_string(True))

    async def async_turn_off(self, **kwargs):
        """Turn the device off.

        This method is a coroutine.
        """
        self._node.get_property(PROP_ON).set_state(bool_to_string(False))

    @property
    def available(self):
        """Return if the device is available."""
        return self._node.device.online

    @property
    def should_poll(self):
        return False
