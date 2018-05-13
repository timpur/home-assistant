"""Homie Component"""

import logging
import voluptuous as vol
from homie import Homie
from homie.models import (HomieDevice, HomieNode)
from homie.tools.constants import (TYPE_SENSOR, TYPE_SWITCH, TYPE_LIGHT)
import homeassistant.components.mqtt as mqtt
from homeassistant.components.mqtt import (
    CONF_DISCOVERY_PREFIX,
    CONF_QOS,
    valid_publish_topic,
    _VALID_QOS_SCHEMA
)
from homeassistant.helpers.typing import (HomeAssistantType, ConfigType)
from homeassistant.helpers.discovery import load_platform
from homeassistant.exceptions import HomeAssistantError
from typing import Callable


# GLOBALS
_LOGGER = logging.getLogger(__name__)
DOMAIN = 'homie'
# REQUIREMENTS = ['homie']
DEPENDENCIES = ['mqtt']

KEY_HOMIE_CONTROLLER = 'homie_controller'
KEY_HOMIE_DISCOVERED = 'homie_discovered'
KEY_HOMIE_ENTITY_ID = 'homie_entity_name'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_DISCOVERY_PREFIX, default=None): valid_publish_topic,
        vol.Optional(CONF_QOS, default=None): _VALID_QOS_SCHEMA,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass: HomeAssistantType, config: ConfigType):
    """Setup the Homie Component."""
    # Init
    hass.data[DOMAIN] = dict()
    hass.data[DOMAIN][KEY_HOMIE_DISCOVERED] = dict()

    # Config
    conf = config.get(DOMAIN)
    if conf is None:
        conf = CONFIG_SCHEMA({DOMAIN: {}})[DOMAIN]

    discovery_prefix = conf.get(CONF_DISCOVERY_PREFIX)
    qos = conf.get(CONF_QOS)

    def _on_homie_device_discovery(homie_device: HomieDevice, stage):
        _LOGGER.info(
            f"Homie device discovered: {homie_device.device_id}:{stage}")
        _setup_device(homie_device)
        for homie_node in homie_device.nodes:
            _setup_node(homie_node)

    def _setup_device(device: HomieDevice):
        pass

    def _setup_node(node: HomieNode):
        if node.type.startswith(TYPE_SENSOR):
            _setup_device_node_as_platform(node, 'sensor')
        elif node.type.startswith(TYPE_SWITCH):
            _setup_device_node_as_platform(node, 'switch')
        elif node.type.startswith(TYPE_LIGHT):
            _setup_device_node_as_platform(node, 'light')

    def _setup_device_node_as_platform(node: HomieNode, platform: str):
        hass.data[DOMAIN][KEY_HOMIE_DISCOVERED][node.entity_id] = node
        discovery_info = {KEY_HOMIE_ENTITY_ID: node.entity_id}
        load_platform(hass, platform, DOMAIN, discovery_info)

    homie_controller = Homie(MQTTWrapper(hass), discovery_prefix, qos)
    homie_controller.set_on_device_discovery(_on_homie_device_discovery)
    homie_controller.start()

    hass.data[DOMAIN][KEY_HOMIE_CONTROLLER] = homie_controller

    return True


class MQTTWrapper(object):
    def __init__(self, hass):
        super().__init__()
        self._hass = hass

    def publish(self, topic: str, payload, qos: int, retain: bool = False) -> int:
        mqtt.publish(self._hass, topic, payload, qos, retain)
        return -1

    def subscribe(self, topic: str, msg_callback, qos: int, encoding: str = 'utf-8') -> Callable[[], None]:
        return mqtt.subscribe(self._hass, topic, msg_callback, qos, encoding)


class PlatformBindError(HomeAssistantError):
    def __init__(self):
        super().__init__("Homie Sensor faild to recive a Homie Node to bind too")
