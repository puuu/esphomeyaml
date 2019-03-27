import voluptuous as vol

from esphome.automation import ACTION_REGISTRY, CONDITION_REGISTRY, maybe_simple_id
from esphome.components import mqtt
from esphome.components.mqtt import setup_mqtt_component
import esphome.config_validation as cv
from esphome.const import CONF_ACCURACY_DECIMALS, CONF_CURRENT_TEMPERATURE, \
    CONF_CURRENT_TEMPERATURE_STATE_TOPIC, CONF_ID, CONF_IS, CONF_INITIAL, CONF_INTERNAL, \
    CONF_MAX, CONF_MIN, CONF_MODE, CONF_MODE_COMMAND_TOPIC, CONF_MODE_STATE_TOPIC, \
    CONF_MQTT_ID, CONF_UPDATE_INTERVAL, CONF_STEP_SIZE, CONF_TARGET_TEMPERATURE, \
    CONF_TARGET_TEMPERATURE_COMMAND_TOPIC, CONF_TARGET_TEMPERATURE_STATE_TOPIC
from esphome.core import CORE
from esphome.cpp_generator import Pvariable, add, get_variable, templatable
from esphome.cpp_types import Action, PollingComponent, Nameable, float_, esphome_ns
from esphome.py_compat import string_types

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({

})

climatedevice_ns = esphome_ns.namespace('climatedevice')
ClimateDevice = climatedevice_ns.class_('ClimateDevice', Nameable, PollingComponent)
MQTTClimateDeviceComponent = climatedevice_ns.class_('MQTTClimateDeviceComponent',
                                                     mqtt.MQTTComponent)

# Actions
PublishAction = climatedevice_ns.class_('PublishAction', Action)
ControlAction = climatedevice_ns.class_('ControlAction', Action)
CurrentTemperatureAction = climatedevice_ns.class_('CurrentTemperatureAction', Action)

# Conditions
ModeCondition = climatedevice_ns.class_('ModeCondition')

ClimateDeviceMode = climatedevice_ns.enum('ClimateDeviceMode')
CLIMATEDEVICE_MODE_OFF = ClimateDeviceMode.CLIMATEDEVICE_MODE_OFF
CLIMATEDEVICE_MODE_AUTO = ClimateDeviceMode.CLIMATEDEVICE_MODE_AUTO
CLIMATEDEVICE_MODE_COOL = ClimateDeviceMode.CLIMATEDEVICE_MODE_COOL
CLIMATEDEVICE_MODE_HEAT = ClimateDeviceMode.CLIMATEDEVICE_MODE_HEAT

ClimateDeviceState = climatedevice_ns.struct('ClimateDeviceState')


def validate_target_temperature(value):
    min_temperature = value.get(CONF_MIN)
    max_temperature = value.get(CONF_MAX)
    if max_temperature < min_temperature:
        raise vol.Invalid("Max temperature ({}) must be larger than min temperature ({})."
                          "".format(max_temperature, min_temperature))
    if CONF_INITIAL in value:
        if not min_temperature <= value[CONF_INITIAL] <= max_temperature:
            raise vol.Invalid("Initial target temperature ({}) must be in the given range of {} and"
                              " {}".format(value[CONF_INITIAL], min_temperature, max_temperature))
    if CONF_STEP_SIZE in value:
        if (max_temperature - min_temperature) < value[CONF_STEP_SIZE]:
            raise vol.Invalid("Step size of target temperature ({}) must be smaller than the "
                              "min max range ({})".format(value[CONF_STEP_SIZE],
                                                          max_temperature - min_temperature))
    return value


CLIMATEDEVICE_SCHEMA = cv.MQTT_COMPONENT_SCHEMA.extend({
    cv.GenerateID(): cv.declare_variable_id(ClimateDevice),
    cv.GenerateID(CONF_MQTT_ID): cv.declare_variable_id(ClimateDevice),
    vol.Optional(CONF_CURRENT_TEMPERATURE_STATE_TOPIC): vol.All(cv.requires_component('mqtt'),
                                                                cv.publish_topic),
    vol.Optional(CONF_MODE_STATE_TOPIC): vol.All(cv.requires_component('mqtt'),
                                                 cv.publish_topic),
    vol.Optional(CONF_MODE_COMMAND_TOPIC): vol.All(cv.requires_component('mqtt'),
                                                   cv.subscribe_topic),
    vol.Optional(CONF_TARGET_TEMPERATURE_STATE_TOPIC): vol.All(cv.requires_component('mqtt'),
                                                               cv.publish_topic),
    vol.Optional(CONF_TARGET_TEMPERATURE_COMMAND_TOPIC): vol.All(cv.requires_component('mqtt'),
                                                                 cv.subscribe_topic),
    vol.Optional(CONF_TARGET_TEMPERATURE): vol.All(cv.Schema({
        vol.Optional(CONF_ACCURACY_DECIMALS): vol.Coerce(int),
        vol.Optional(CONF_INITIAL): cv.float_,
        vol.Optional(CONF_STEP_SIZE): cv.float_,
        vol.Optional(CONF_MIN, default=10): cv.float_,
        vol.Optional(CONF_MAX, default=30): cv.float_,
    }), validate_target_temperature),
    vol.Optional(CONF_ACCURACY_DECIMALS): vol.Coerce(int),
    vol.Optional(CONF_UPDATE_INTERVAL): cv.update_interval,
})

CLIMATEDEVICE_PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(CLIMATEDEVICE_SCHEMA.schema)

CLIMATEDEVICE_MODES = {
    'OFF': CLIMATEDEVICE_MODE_OFF,
    'AUTO': CLIMATEDEVICE_MODE_AUTO,
    'COOL': CLIMATEDEVICE_MODE_COOL,
    'HEAT': CLIMATEDEVICE_MODE_HEAT,
}


def setup_climatedevice_core_(climatedevice_var, config):
    if CONF_INTERNAL in config:
        add(climatedevice_var.set_internal(config[CONF_INTERNAL]))
    if CONF_UPDATE_INTERVAL in config:
        add(climatedevice_var.set_update_interval(config[CONF_UPDATE_INTERVAL]))
    if CONF_ACCURACY_DECIMALS in config:
        add(climatedevice_var.set_current_temperature_accuracy_decimals(
            config[CONF_ACCURACY_DECIMALS]))

    if CONF_TARGET_TEMPERATURE in config:
        target_temperature = config[CONF_TARGET_TEMPERATURE]
        if CONF_ACCURACY_DECIMALS in target_temperature:
            add(climatedevice_var.set_target_temperature_accuracy_decimals(
                target_temperature[CONF_ACCURACY_DECIMALS]))
        if CONF_INITIAL in target_temperature:
            add(climatedevice_var.set_target_temperature_initial(target_temperature[CONF_INITIAL]))
        if CONF_STEP_SIZE in target_temperature:
            add(climatedevice_var.set_target_temperature_step(target_temperature[CONF_STEP_SIZE]))
        if CONF_MIN in target_temperature and CONF_MAX in target_temperature:
            add(climatedevice_var.set_target_temperature_range(target_temperature[CONF_MIN],
                                                               target_temperature[CONF_MAX]))

    mqtt_ = climatedevice_var.Pget_mqtt()
    if CONF_CURRENT_TEMPERATURE_STATE_TOPIC in config:
        add(mqtt_.set_custom_current_temperature_state_topic(
            config[CONF_CURRENT_TEMPERATURE_STATE_TOPIC]))
    if CONF_MODE_STATE_TOPIC in config:
        add(mqtt_.set_custom_mode_state_topic([CONF_MODE_STATE_TOPIC]))
    if CONF_MODE_COMMAND_TOPIC in config:
        add(mqtt_.set_custom_mode_command_topic(config[CONF_MODE_COMMAND_TOPIC]))
    if CONF_TARGET_TEMPERATURE_STATE_TOPIC in config:
        add(mqtt_.set_custom_target_temperature_state_topic(
            config[CONF_TARGET_TEMPERATURE_STATE_TOPIC]))
    if CONF_TARGET_TEMPERATURE_COMMAND_TOPIC in config:
        add(mqtt_.set_custom_targer_temperature_command_topic(
            config[CONF_TARGET_TEMPERATURE_COMMAND_TOPIC]))
    setup_mqtt_component(mqtt_, config)


def setup_climatedevice(climatedevice_obj, config):
    CORE.add_job(setup_climatedevice_core_, climatedevice_obj, config)


BUILD_FLAGS = '-DUSE_CLIMATEDEVICE'

CONF_CLIMATEDEVICE_PUBLISH = 'climatedevice.publish'
CLIMATEDEVICE_PUBLISH_ACTION_SCHEMA = vol.All({
    vol.Required(CONF_ID): cv.use_variable_id(ClimateDevice),
    vol.Optional(CONF_MODE): cv.templatable(cv.one_of(*CLIMATEDEVICE_MODES, upper=True)),
    vol.Optional(CONF_TARGET_TEMPERATURE): cv.templatable(cv.float_),
}, cv.has_at_least_one_key(CONF_MODE, CONF_TARGET_TEMPERATURE))


@ACTION_REGISTRY.register(CONF_CLIMATEDEVICE_PUBLISH, CLIMATEDEVICE_PUBLISH_ACTION_SCHEMA)
def climatedevice_publish_to_code(config, action_id, template_arg, args):
    for var in get_variable(config[CONF_ID]):
        yield None
    rhs = var.make_publish_action(template_arg)
    type = PublishAction.template(template_arg)
    action = Pvariable(action_id, rhs, type=type)
    if CONF_MODE in config:
        for template_ in templatable(config[CONF_MODE], args, ClimateDeviceMode):
            yield None
        # TODO: Why does the return type resolve to climatedevice and
        #       not climatedevice::ClimateDeviceMode ?
        if isinstance(template_, string_types):
            template_ = CLIMATEDEVICE_MODES[template_]
        add(action.set_mode(template_))
    if CONF_TARGET_TEMPERATURE in config:
        for template_ in templatable(config[CONF_TARGET_TEMPERATURE], args, float_):
            yield None
        add(action.set_target_temperature(template_))
    yield action


CONF_CLIMATEDEVICE_CONTROL = 'climatedevice.control'
CLIMATEDEVICE_CONTROL_ACTION_SCHEMA = CLIMATEDEVICE_PUBLISH_ACTION_SCHEMA


@ACTION_REGISTRY.register(CONF_CLIMATEDEVICE_CONTROL, CLIMATEDEVICE_CONTROL_ACTION_SCHEMA)
def climatedevice_perform_to_code(config, action_id, template_arg, args):
    for var in get_variable(config[CONF_ID]):
        yield None
    rhs = var.make_control_action(template_arg)
    type = ControlAction.template(template_arg)
    action = Pvariable(action_id, rhs, type=type)
    if CONF_MODE in config:
        for template_ in templatable(config[CONF_MODE], args, ClimateDeviceMode):
            yield None
        if isinstance(template_, string_types):
            template_ = CLIMATEDEVICE_MODES[template_]
        add(action.set_mode(template_))
    if CONF_TARGET_TEMPERATURE in config:
        for template_ in templatable(config[CONF_TARGET_TEMPERATURE], args, float_):
            yield None
        add(action.set_target_temperature(template_))
    yield action


CONF_CLIMATEDEVICE_CURRENT_TEMPERATUR = 'climatedevice.current_temperature'
CLIMATEDEVICE_CURRENT_TEMPERATUR_ACTION_SCHEMA = cv.Schema({
    vol.Required(CONF_ID): cv.use_variable_id(ClimateDevice),
    vol.Required(CONF_CURRENT_TEMPERATURE): cv.templatable(cv.float_),
})


@ACTION_REGISTRY.register(CONF_CLIMATEDEVICE_CURRENT_TEMPERATUR,
                          CLIMATEDEVICE_CURRENT_TEMPERATUR_ACTION_SCHEMA)
def climatedevice_current_temperature_to_code(config, action_id, template_arg, args):
    for var in get_variable(config[CONF_ID]):
        yield None
    rhs = var.make_current_temperature_action(template_arg)
    type = CurrentTemperatureAction.template(template_arg)
    action = Pvariable(action_id, rhs, type=type)
    for template_ in templatable(config[CONF_CURRENT_TEMPERATURE], args, float_):
        yield None
    add(action.set_current_temperature(template_))
    yield action


CONF_CLIMATEDEVICE_MODE = 'climatedevice.mode'
CLIMATEDEVICE_MODE_CONDITION_SCHEMA = maybe_simple_id({
    vol.Required(CONF_ID): cv.use_variable_id(ClimateDevice),
    vol.Optional(CONF_IS): cv.one_of(*CLIMATEDEVICE_MODES, upper=True),
})


@CONDITION_REGISTRY.register(CONF_CLIMATEDEVICE_MODE, CLIMATEDEVICE_MODE_CONDITION_SCHEMA)
def climatedevice_mode_to_code(config, condition_id, template_arg, args):
    for var in get_variable(config[CONF_ID]):
        yield None
    rhs = var.make_mode_condition(template_arg)
    type = ModeCondition.template(template_arg)
    cond = Pvariable(condition_id, rhs, type=type)
    if CONF_IS in config:
        add(cond.set_mode(CLIMATEDEVICE_MODES[config[CONF_IS]]))
    yield cond
