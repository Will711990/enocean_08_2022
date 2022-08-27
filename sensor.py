"""Support for EnOcean sensors."""
from __future__ import annotations
import time

from collections.abc import Callable
from dataclasses import dataclass

from enocean.utils import combine_hex
import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ID,
    CONF_NAME,
    PERCENTAGE,
    POWER_WATT,
    STATE_CLOSED,
    STATE_OPEN,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .device import EnOceanEntity

CONF_MAX_TEMP = "max_temp"
CONF_MIN_TEMP = "min_temp"
CONF_RANGE_FROM = "range_from"
CONF_RANGE_TO = "range_to"

DEFAULT_NAME = "EnOcean sensor"

SENSOR_TYPE_HUMIDITY = "humidity"
SENSOR_TYPE_POWER = "powersensor"
SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_WINDOWHANDLE = "windowhandle"
SENSOR_TYPE_DOORDETECTOR = "doordetector"
SENSOR_TYPE_MOTIONDETECTOR = "motiondetector"
SENSOR_TYPE_SOFTBUTTON = "softbutton"
SENSOR_TYPE_SOFTREMOTE = "softremote"

@dataclass
class EnOceanSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    unique_id: Callable[[list[int]], str | None]


@dataclass
class EnOceanSensorEntityDescription(
    SensorEntityDescription, EnOceanSensorEntityDescriptionMixin
):
    """Describes EnOcean sensor entity."""


SENSOR_DESC_TEMPERATURE = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_TEMPERATURE,
    name="Temperature",
    native_unit_of_measurement=TEMP_CELSIUS,
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_TEMPERATURE}",
)

SENSOR_DESC_HUMIDITY = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_HUMIDITY,
    name="Humidity",
    native_unit_of_measurement=PERCENTAGE,
    icon="mdi:water-percent",
    device_class=SensorDeviceClass.HUMIDITY,
    state_class=SensorStateClass.MEASUREMENT,
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_HUMIDITY}",
)

SENSOR_DESC_POWER = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_POWER,
    name="Power",
    native_unit_of_measurement=POWER_WATT,
    icon="mdi:power-plug",
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_POWER}",
)

SENSOR_DESC_WINDOWHANDLE = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_WINDOWHANDLE,
    name="WindowHandle",
    icon="mdi:window-open-variant",
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_WINDOWHANDLE}",
)

SENSOR_DESC_DOORDETECTOR = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_DOORDETECTOR,
    name="DoorDetector",
    icon="mdi:door-closed",
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_DOORDETECTOR}",
)

SENSOR_DESC_MOTIONDETECTOR = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_MOTIONDETECTOR,
    name="MotionDetector",
    icon="mdi:motion-sensor",
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_MOTIONDETECTOR}",
)

SENSOR_DESC_SOFTBUTTON = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_SOFTBUTTON,
    name="SoftButton",
    icon="mdi:radiobox-marked",
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_SOFTBUTTON}",
)

SENSOR_DESC_SOFTREMOTE = EnOceanSensorEntityDescription(
    key=SENSOR_TYPE_SOFTREMOTE,
    name="SoftRemote",
    icon="mdi:remote-tv",
    unique_id=lambda dev_id: f"{combine_hex(dev_id)}-{SENSOR_TYPE_SOFTREMOTE}",
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS, default=SENSOR_TYPE_POWER): cv.string,
        vol.Optional(CONF_MAX_TEMP, default=40): vol.Coerce(int),
        vol.Optional(CONF_MIN_TEMP, default=0): vol.Coerce(int),
        vol.Optional(CONF_RANGE_FROM, default=255): cv.positive_int,
        vol.Optional(CONF_RANGE_TO, default=0): cv.positive_int,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an EnOcean sensor device."""
    dev_id = config[CONF_ID]
    dev_name = config[CONF_NAME]
    sensor_type = config[CONF_DEVICE_CLASS]

    entities: list[EnOceanSensor] = []
    if sensor_type == SENSOR_TYPE_TEMPERATURE:
        temp_min = config[CONF_MIN_TEMP]
        temp_max = config[CONF_MAX_TEMP]
        range_from = config[CONF_RANGE_FROM]
        range_to = config[CONF_RANGE_TO]
        entities = [
            EnOceanTemperatureSensor(
                dev_id,
                dev_name,
                SENSOR_DESC_TEMPERATURE,
                scale_min=temp_min,
                scale_max=temp_max,
                range_from=range_from,
                range_to=range_to,
            )
        ]

    elif sensor_type == SENSOR_TYPE_HUMIDITY:
        entities = [EnOceanHumiditySensor(dev_id, dev_name, SENSOR_DESC_HUMIDITY)]

    elif sensor_type == SENSOR_TYPE_POWER:
        entities = [EnOceanPowerSensor(dev_id, dev_name, SENSOR_DESC_POWER)]

    elif sensor_type == SENSOR_TYPE_WINDOWHANDLE:
        entities = [EnOceanWindowHandle(dev_id, dev_name, SENSOR_DESC_WINDOWHANDLE)]

    elif sensor_type == SENSOR_TYPE_DOORDETECTOR:
        entities = [EnOceanDoorDetector(dev_id, dev_name, SENSOR_DESC_DOORDETECTOR)]

    elif sensor_type == SENSOR_TYPE_MOTIONDETECTOR:
        entities = [EnOceanMotionDetector(dev_id, dev_name, SENSOR_DESC_MOTIONDETECTOR)]

    elif sensor_type == SENSOR_TYPE_SOFTBUTTON:
        entities = [EnOceanSoftButton(dev_id, dev_name, SENSOR_DESC_SOFTBUTTON)]

    elif sensor_type == SENSOR_TYPE_SOFTREMOTE:
        entities = [EnOceanSoftRemote(dev_id, dev_name, SENSOR_DESC_SOFTREMOTE)]

    if entities:
        add_entities(entities)


class EnOceanSensor(EnOceanEntity, RestoreEntity, SensorEntity):
    """Representation of an  EnOcean sensor device such as a power meter."""

    def __init__(self, dev_id, dev_name, description: EnOceanSensorEntityDescription):
        """Initialize the EnOcean sensor device."""
        super().__init__(dev_id, dev_name)
        self.entity_description = description
        self._attr_name = f"{description.name} {dev_name}"
        self._attr_unique_id = description.unique_id(dev_id)

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        # If not None, we got an initial value.
        await super().async_added_to_hass()
        if self._attr_native_value is not None:
            return

        if (state := await self.async_get_last_state()) is not None:
            self._attr_native_value = state.state

    def value_changed(self, packet):
        """Update the internal state of the sensor."""


class EnOceanPowerSensor(EnOceanSensor):
    """Representation of an EnOcean power sensor.

    EEPs (EnOcean Equipment Profiles):
    - A5-12-01 (Automated Meter Reading, Electricity)
    """

    def value_changed(self, packet):
        """Update the internal state of the sensor."""
        if packet.rorg != 0xA5:
            return
        packet.parse_eep(0x12, 0x01)
        if packet.parsed["DT"]["raw_value"] == 1:
            # this packet reports the current value
            raw_val = packet.parsed["MR"]["raw_value"]
            divisor = packet.parsed["DIV"]["raw_value"]
            self._attr_native_value = raw_val / (10**divisor)
            self.schedule_update_ha_state()


class EnOceanTemperatureSensor(EnOceanSensor):
    """Representation of an EnOcean temperature sensor device.

    EEPs (EnOcean Equipment Profiles):
    - A5-02-01 to A5-02-1B All 8 Bit Temperature Sensors of A5-02
    - A5-10-01 to A5-10-14 (Room Operating Panels)
    - A5-04-01 (Temp. and Humidity Sensor, Range 0°C to +40°C and 0% to 100%)
    - A5-04-02 (Temp. and Humidity Sensor, Range -20°C to +60°C and 0% to 100%)
    - A5-10-10 (Temp. and Humidity Sensor and Set Point)
    - A5-10-12 (Temp. and Humidity Sensor, Set Point and Occupancy Control)
    - 10 Bit Temp. Sensors are not supported (A5-02-20, A5-02-30)

    For the following EEPs the scales must be set to "0 to 250":
    - A5-04-01
    - A5-04-02
    - A5-10-10 to A5-10-14
    """

    def __init__(
        self,
        dev_id,
        dev_name,
        description: EnOceanSensorEntityDescription,
        *,
        scale_min,
        scale_max,
        range_from,
        range_to,
    ):
        """Initialize the EnOcean temperature sensor device."""
        super().__init__(dev_id, dev_name, description)
        self._scale_min = scale_min
        self._scale_max = scale_max
        self.range_from = range_from
        self.range_to = range_to

    def value_changed(self, packet):
        """Update the internal state of the sensor."""
        if packet.data[0] != 0xA5:
            return
        temp_scale = self._scale_max - self._scale_min
        temp_range = self.range_to - self.range_from
        raw_val = packet.data[3]
        temperature = temp_scale / temp_range * (raw_val - self.range_from)
        temperature += self._scale_min
        self._attr_native_value = round(temperature, 1)
        self.schedule_update_ha_state()


class EnOceanHumiditySensor(EnOceanSensor):
    """Representation of an EnOcean humidity sensor device.

    EEPs (EnOcean Equipment Profiles):
    - A5-04-01 (Temp. and Humidity Sensor, Range 0°C to +40°C and 0% to 100%)
    - A5-04-02 (Temp. and Humidity Sensor, Range -20°C to +60°C and 0% to 100%)
    - A5-10-10 to A5-10-14 (Room Operating Panels)
    """

    def value_changed(self, packet):
        """Update the internal state of the sensor."""
        if packet.rorg != 0xA5:
            return
        humidity = packet.data[2] * 100 / 250
        self._attr_native_value = round(humidity, 1)
        self.schedule_update_ha_state()


class EnOceanWindowHandle(EnOceanSensor):
    """Representation of an EnOcean window handle device.
    EEPs (EnOcean Equipment Profiles):
    - F6-10-00 (Mechanical handle / Hoppe AG)
    """

    def value_changed(self, packet):
        """Update the internal state of the sensor."""
        action = (packet.data[1] & 0x70) >> 4

        if action == 0x07:
            self._attr_native_value = STATE_CLOSED
        if action in (0x04, 0x06):
            self._attr_native_value = STATE_OPEN
        if action == 0x05:
            self._attr_native_value = "tilt"

        self.schedule_update_ha_state()

class EnOceanDoorDetector(EnOceanSensor):
    """Representation of an EnOcean window handle device.

    EEPs (EnOcean Equipment Profiles):
    - D5-00-01
    """

    def value_changed(self, packet):

        """Update the internal state of the sensor."""
        packet.parse_eep(0x00, 0x01)
        contact_value = packet.parsed['CO']['value']

        if contact_value == 'open':
            self._attr_native_value = STATE_OPEN
        elif contact_value == 'closed':
            self._attr_native_value = STATE_CLOSED

        self.schedule_update_ha_state()

class EnOceanMotionDetector(EnOceanSensor):

    def value_changed(self, packet):
        if packet.rorg == 0xA5:
            action = packet.data[4]
    
            if action == 0x08:
                self._attr_native_value = 0
            if action == 0x88:
                self._attr_native_value = 1
            else:
                self._attr_native_value = 0

        self.schedule_update_ha_state()

class EnOceanSoftButton(EnOceanSensor):

    def value_changed(self, packet):

        if packet.rorg == 0xD2:
            press = packet.data[2]
            if press == 0x01:
                self._attr_native_value = 1
                self.schedule_update_ha_state()
                time.sleep(1)
                self._attr_native_value = 0
                self.schedule_update_ha_state()
            elif press == 0x02:
                self._attr_native_value = 2
                self.schedule_update_ha_state()
                time.sleep(1)
                self._attr_native_value = 0
                self.schedule_update_ha_state()
            elif press == 0x03:
                self._attr_native_value = 3
                self.schedule_update_ha_state()
                time.sleep(1)
                self._attr_native_value = 0
                self.schedule_update_ha_state()
            else:
                self._attr_native_value = 0
                self.schedule_update_ha_state()

        self.schedule_update_ha_state()

class EnOceanSoftRemote(EnOceanSensor):
    """Representation of an EnOcean window handle device.

    EEPs (EnOcean Equipment Profiles):
    - F6-10-00 (Mechanical handle / Hoppe AG)
    """

    def value_changed(self, packet):
        """Update the internal state of the sensor."""

        if packet.rorg == 0xF6:
            press = packet.data[1]
            if press == 0x70:
                self._attr_native_value = 4
                self.schedule_update_ha_state()
                time.sleep(1)
                self._attr_native_value = 0
                self.schedule_update_ha_state()
            elif press == 0x50:
                self._attr_native_value = 3
                self.schedule_update_ha_state()
                time.sleep(1)
                self._attr_native_value = 0
                self.schedule_update_ha_state()
            elif press == 0x30:
                self._attr_native_value = 2
                self.schedule_update_ha_state()
                time.sleep(1)
                self._attr_native_value = 0
                self.schedule_update_ha_state()
            elif press == 0x10:
                self._attr_native_value = 1
                self.schedule_update_ha_state()
                time.sleep(1)
                self._attr_native_value = 0
                self.schedule_update_ha_state()
            else:
                self._attr_native_value = 0
                self.schedule_update_ha_state()

        self.schedule_update_ha_state()