import voluptuous as vol

from esphome import automation
from esphome.components import climatedevice
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_NAME, CONF_OPTIMISTIC, \
    CONF_CONTROL_ACTION, CONF_ERROR_VALUE_ACTION, CONF_HAS_CURRENT_TEMPERATURE, \
    CONF_MODES, CONF_MODE_LAMBDA, CONF_TARGET_TEMPERATURE_LAMBDA
from esphome.cpp_generator import Pvariable, add, process_lambda
from esphome.cpp_helpers import setup_component
from esphome.cpp_types import App, optional, float_

TemplateClimateDevice = climatedevice.climatedevice_ns.class_('TemplateClimateDevice',
                                                              climatedevice.ClimateDevice)

PLATFORM_SCHEMA = cv.nameable(climatedevice.CLIMATEDEVICE_PLATFORM_SCHEMA.extend({
    cv.GenerateID(): cv.declare_variable_id(TemplateClimateDevice),
    vol.Optional(CONF_MODE_LAMBDA): cv.lambda_,
    vol.Optional(CONF_TARGET_TEMPERATURE_LAMBDA): cv.lambda_,
    vol.Optional(CONF_OPTIMISTIC): cv.boolean,
    vol.Optional(CONF_MODES): cv.ensure_list(cv.one_of(*climatedevice.CLIMATEDEVICE_MODES,
                                                       upper=True)),
    vol.Optional(CONF_HAS_CURRENT_TEMPERATURE): cv.boolean,
    vol.Optional(CONF_CONTROL_ACTION): automation.validate_automation(single=True),
    vol.Optional(CONF_ERROR_VALUE_ACTION): automation.validate_automation(single=True),
}).extend(cv.COMPONENT_SCHEMA.schema))


def to_code(config):
    rhs = App.make_template_climatedevice(config[CONF_NAME])
    var = Pvariable(config[CONF_ID], rhs)

    climatedevice.setup_climatedevice(var, config)
    setup_component(var, config)

    if CONF_MODE_LAMBDA in config:
        for template_ in process_lambda(config[CONF_MODE_LAMBDA], [],
                                        return_type=optional.template(
                                            climatedevice.ClimateDeviceMode)):
            yield
        # TODO: Why does the return type resolve to optional<climatedevice> and
        #       not optional<climatedevice::ClimateDeviceMode> ?
        add(var.set_mode_lambda(template_))
    if CONF_TARGET_TEMPERATURE_LAMBDA in config:
        for template_ in process_lambda(config[CONF_TARGET_TEMPERATURE_LAMBDA], [],
                                        return_type=optional.template(float_)):
            yield
        add(var.set_target_temperature_lambda(template_))
    if CONF_MODES in config:
        modes = [climatedevice.CLIMATEDEVICE_MODES[mode] for mode in config[CONF_MODES]]
        add(var.set_modes(modes))
    if CONF_CONTROL_ACTION in config:
        automation.build_automations(var.get_control_trigger(),
                                     [(climatedevice.ClimateDeviceState, 'x')],
                                     config[CONF_CONTROL_ACTION])
    if CONF_ERROR_VALUE_ACTION in config:
        automation.build_automations(var.get_error_value_trigger(), [(float_, 'x')],
                                     config[CONF_ERROR_VALUE_ACTION])
    if CONF_OPTIMISTIC in config:
        add(var.set_optimistic(config[CONF_OPTIMISTIC]))
    if CONF_HAS_CURRENT_TEMPERATURE in config:
        add(var.set_current_temperature_support(config[CONF_HAS_CURRENT_TEMPERATURE]))


BUILD_FLAGS = '-DUSE_TEMPLATE_CLIMATEDEVICE'
