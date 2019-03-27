import voluptuous as vol

from esphome.components import climatedevice, output
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_NAME, CONF_OUTPUT, \
    CONF_COLD, CONF_COOLING, CONF_HOT, CONF_HYSTERESIS, CONF_MIN_CYCLE_DURATION
from esphome.cpp_generator import Pvariable, get_variable, add
from esphome.cpp_helpers import setup_component
from esphome.cpp_types import App

ThermostatClimateDevice = climatedevice.climatedevice_ns.class_('ThermostatClimateDevice',
                                                                climatedevice.ClimateDevice)

HYSTERESIS_SCHEMA = cv.Schema({
    vol.Required(CONF_COLD): cv.float_,
    vol.Required(CONF_HOT): cv.float_,
})


def hysteresis_schema(value):
    if isinstance(value, dict):
        return HYSTERESIS_SCHEMA(value)
    hysteresis = cv.float_(value)
    return {CONF_COLD: hysteresis, CONF_HOT: hysteresis}


PLATFORM_SCHEMA = cv.nameable(climatedevice.CLIMATEDEVICE_PLATFORM_SCHEMA.extend({
    cv.GenerateID(): cv.declare_variable_id(ThermostatClimateDevice),
    vol.Required(CONF_OUTPUT): cv.use_variable_id(output.BinaryOutput),
    vol.Optional(CONF_COOLING): cv.boolean,
    vol.Optional(CONF_HYSTERESIS): hysteresis_schema,
    vol.Optional(CONF_MIN_CYCLE_DURATION): cv.positive_time_period_milliseconds,
}))


def to_code(config):
    for output_ in get_variable(config[CONF_OUTPUT]):
        yield
    rhs = App.make_thermostat_climatedevice(config[CONF_NAME], output_)
    var = Pvariable(config[CONF_ID], rhs)

    climatedevice.setup_climatedevice(var, config)
    setup_component(var, config)

    if CONF_COOLING in config:
        add(var.set_cooling(config[CONF_COOLING]))
    if CONF_HYSTERESIS in config:
        hysteresis = config[CONF_HYSTERESIS]
        add(var.set_hysteresis(hysteresis[CONF_COLD], hysteresis[CONF_HOT]))
    if CONF_MIN_CYCLE_DURATION in config:
        add(var.set_min_cycle_duration(config[CONF_MIN_CYCLE_DURATION]))


BUILD_FLAGS = '-DUSE_THERMOSTAT_CLIMATEDEVICE'
