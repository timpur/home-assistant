"""HA Homie Light Module"""

import logging

from homie.tools.constants import (
    TYPE_LIGHT,
    TYPE_LIGHT_RGB,
    PROP_ON,
    PROP_BRIGHTNESS,
    PROP_RGB
)
from homie.tools.helpers import (
    check_node_has_prop,
    string_to_bool,
    bool_to_string
)
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.components.light import (Light, ENTITY_ID_FORMAT)
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
    """Set up the Homie Light."""
    entity_id = discovery_info[KEY_HOMIE_ENTITY_ID]
    homie_node = hass.data[DOMAIN][KEY_HOMIE_DISCOVERED][entity_id]
    if homie_node is None:
        raise PlatformBindError()
    check_node_has_prop('Switch', homie_node, PROP_ON)
    check_node_has_prop('Switch', homie_node, PROP_BRIGHTNESS)
    if homie_node.type == TYPE_LIGHT_RGB:
        check_node_has_prop('Switch', homie_node, PROP_RGB)

    _LOGGER.info(f"Setting up Homie Light: {entity_id}")
    async_add_entities([HomieLight(hass, entity_id, homie_node)])


class HomieLight(Light):
    """Implementation of a Homie Light."""

    def __init__(self, hass, entity_id: str, homie_node: HomieNode):
        """Initialize Homie Light."""
        self._id = entity_id
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, entity_id, hass=hass)
        self._node = homie_node
        self._node.device.add_attribute_listener(self._on_change, '_online')
        self._node.get_property(
            PROP_ON).add_attribute_listener(self._on_change)
        self._node.get_property(
            PROP_BRIGHTNESS).add_attribute_listener(self._on_change)

    def _on_change(self, obj, name, pre, value):
        self.async_schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the Homie Light."""
        return self._id

    @property
    def is_on(self):
        """Returns true if the Homie Light is on."""
        return string_to_bool(self._node.get_property(PROP_ON).state)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return int(self._node.get_property(PROP_BRIGHTNESS).state)

    async def async_turn_on(self, **kwargs):
        """
        Turn the device on.

        This method is a coroutine.
        """
        self._node.get_property(PROP_ON).set_state(bool_to_string(True))

    async def async_turn_off(self, **kwargs):
        """
        Turn the device off.

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
